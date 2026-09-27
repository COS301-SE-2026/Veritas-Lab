from app.auth.auth import (
    validate_email,
    validate_password,
    verify_jwt,
    ALGORITHM
)
from app.auth import auth
from fastapi import HTTPException

import asyncpg
import pytest
import uuid
from datetime import datetime, timedelta, timezone
from jose import jwt
from unittest.mock import AsyncMock, MagicMock

TEST_SECRET_KEY = "test-secret"
COOKIE_NAME = "JWT_token"
USER_ID = "12345678-abcd-ef01-2345-6789abcdef01"
TOKEN_LIFETIME_MINUTES = 10

def make_request(token: str | None) -> MagicMock:
    """Build a mock FastAPI Request with the JWT cookie set."""
    request = MagicMock()
    request.cookies = {COOKIE_NAME: token} if token else {}
    return request


def make_token(payload_overrides: dict = {}, secret: str = TEST_SECRET_KEY, drop: tuple = ()) -> str:
    base_payload = {
        "sub": USER_ID,
        "username": "byron",
        "role": "ADMIN",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    payload = {**base_payload, **payload_overrides}
    for claim in drop:
        payload.pop(claim)
    return jwt.encode(payload, secret, algorithm=ALGORITHM)

def token_issued_at(issued_at: datetime) -> str:
    """Tokens only carry exp, so a token issued at issued_at expires one lifetime later."""
    return make_token({"exp": issued_at + timedelta(minutes=TOKEN_LIFETIME_MINUTES)})

def stored_user(**overrides) -> dict:
    """The Users row that matches the default token claims."""
    row = {
        "userid": uuid.UUID(USER_ID),
        "username": "byron",
        "userrole": "ADMIN",
        "userjwtissued": None
    }
    return {**row, **overrides}

def make_connection(row: dict | None) -> MagicMock:
    connection = MagicMock()
    connection.fetchrow = AsyncMock(return_value=row)
    return connection

@pytest.fixture(autouse=True)
def fixed_token_settings(monkeypatch):
    monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)
    monkeypatch.setattr(auth.auth_settings, "TOKEN_EXPIRE", TOKEN_LIFETIME_MINUTES)

class TestVerifyJWT:
    @pytest.mark.asyncio
    async def test_valid_token(self):
        connection = make_connection(stored_user())

        decoded = await verify_jwt(make_request(make_token()), connection)

        assert decoded["sub"] == USER_ID
        assert decoded["username"] == "byron"
        assert decoded["role"] == "ADMIN"
        assert connection.fetchrow.await_args.args[1] == USER_ID

    @pytest.mark.asyncio
    async def test_missing_cookie(self):
        connection = make_connection(stored_user())

        with pytest.raises(HTTPException) as excinfo:
            await verify_jwt(make_request(None), connection)

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail["message"] == "Not authenticated"
        connection.fetchrow.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_expired_token(self):
        token = make_token({"exp": datetime.now(timezone.utc) - timedelta(minutes=10)})

        with pytest.raises(HTTPException) as excinfo:
            await verify_jwt(make_request(token), make_connection(stored_user()))

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail["message"] == "Token has expired"

    @pytest.mark.asyncio
    async def test_invalid_token(self):
        with pytest.raises(HTTPException) as excinfo:
            await verify_jwt(make_request("this.is.not.valid"), make_connection(stored_user()))

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail["message"] == "Invalid token"

    @pytest.mark.asyncio
    async def test_wrong_secret(self):
        token = make_token(secret="wrong-secret")

        with pytest.raises(HTTPException) as excinfo:
            await verify_jwt(make_request(token), make_connection(stored_user()))

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail["message"] == "Invalid token"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("overrides, drop", [
        ({"sub": "123"}, ()),
        ({}, ("sub",)),
        ({}, ("username",)),
        ({}, ("role",)),
        ({}, ("exp",)),
    ])
    async def test_malformed_claims_rejected_before_database(self, overrides, drop):
        connection = make_connection(stored_user())

        with pytest.raises(HTTPException) as excinfo:
            await verify_jwt(make_request(make_token(overrides, drop=drop)), connection)

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail["message"] == "Invalid token"
        connection.fetchrow.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_user_not_in_database(self):
        with pytest.raises(HTTPException) as excinfo:
            await verify_jwt(make_request(make_token()), make_connection(None))

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail["message"] == "Invalid token"

    @pytest.mark.asyncio
    async def test_username_does_not_match_database(self):
        connection = make_connection(stored_user(username="not_byron"))

        with pytest.raises(HTTPException) as excinfo:
            await verify_jwt(make_request(make_token()), connection)

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail["message"] == "Invalid token"

    @pytest.mark.asyncio
    async def test_role_does_not_match_database(self):
        # e.g. an admin who has since been demoted still holds a token that says ADMIN
        connection = make_connection(stored_user(userrole="USER"))

        with pytest.raises(HTTPException) as excinfo:
            await verify_jwt(make_request(make_token()), connection)

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail["message"] == "Invalid token"

    @pytest.mark.asyncio
    async def test_database_error(self):
        connection = MagicMock()
        connection.fetchrow = AsyncMock(side_effect=asyncpg.PostgresError("connection lost"))

        with pytest.raises(HTTPException) as excinfo:
            await verify_jwt(make_request(make_token()), connection)

        assert excinfo.value.status_code == 500
        assert excinfo.value.detail["message"] == "Database error"

    @pytest.mark.asyncio
    async def test_token_from_latest_issue_is_accepted(self):
        now = datetime.now(timezone.utc)
        connection = make_connection(stored_user(userjwtissued=now + timedelta(seconds=1)))

        decoded = await verify_jwt(make_request(token_issued_at(now)), connection)

        assert decoded["sub"] == USER_ID

    @pytest.mark.asyncio
    async def test_token_older_than_latest_issue_is_revoked(self):
        now = datetime.now(timezone.utc)
        token = token_issued_at(now - timedelta(minutes=5))
        connection = make_connection(stored_user(userjwtissued=now - timedelta(minutes=1)))

        with pytest.raises(HTTPException) as excinfo:
            await verify_jwt(make_request(token), connection)

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail["message"] == "Invalid token"

    @pytest.mark.asyncio
    async def test_older_token_accepted_within_grace_period(self):
        # A request sent with the old cookie while /api/refresh is issuing a new one
        now = datetime.now(timezone.utc)
        token = token_issued_at(now - timedelta(minutes=5))
        connection = make_connection(stored_user(userjwtissued=now - timedelta(seconds=10)))

        decoded = await verify_jwt(make_request(token), connection)

        assert decoded["sub"] == USER_ID

class TestValidateEmail:
    def test_valid_email(self):
        assert validate_email("u12345678@tuks.co.za") is True

    def test_invalid_email(self):
        assert validate_email("hello world") is False

    def test_empty_email(self):
        assert validate_email("") is False

    def test_email_trimming(self):
        assert validate_email("  u12345678@tuks.co.za  ") is True

    def test_none_email(self):
        assert validate_email(None) is False

    def test_missing_at_symbol(self):
        assert validate_email("userexample.com") is False

    def test_missing_domain(self):
        assert validate_email("user@") is False

    def test_missing_tld(self):
        assert validate_email("user@example") is False

class TestValidatePassword:
    def test_valid_password(self):
        assert validate_password("ThisIsAStrongPassword123@@") is True

    def test_missing_special_char(self):
        assert validate_password("ThisIsAStrongPassword123") is False

    def test_too_short(self):
        assert validate_password("Strong1@") is False

    def test_missing_number(self):
        assert validate_password("@QWertyuipsjdnasndoajd&&saweqwdsadsadffd") is False

    def test_missing_uppercase(self):
        assert validate_password("qwertyuiopasddf123455!@#$sasd") is False

    def test_missing_lowercase(self):
        assert validate_password("QUYGYUGUIHUIGYUGUIHUIHI12345321!##@#$") is False

    def test_empty_password(self):
        assert validate_password("") is False

    def test_none_password(self):
        assert validate_password(None) is False
from app.auth.auth import (
    validate_email,
    validate_password,
    verify_jwt,
    ALGORITHM
)
from fastapi import HTTPException

import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt
from unittest.mock import MagicMock, AsyncMock

TEST_SECRET_KEY = "test-secret"
COOKIE_NAME = "JWT_token"
USER_ID = "11111111-1111-1111-1111-111111111111"

def make_request(token: str | None) -> MagicMock:
    request = MagicMock()
    request.cookies = {COOKIE_NAME: token} if token else {}
    return request

def make_connection(row: dict | None) -> MagicMock:
    connection = MagicMock()
    connection.fetchrow = AsyncMock(return_value=row)
    return connection

def make_token(payload_overrides: dict = {}, secret: str = TEST_SECRET_KEY, drop: tuple = ()) -> str:
    now = datetime.now(timezone.utc)
    base_payload = {
        "sub": USER_ID,
        "username": "byron",
        "role": "ADMIN",
        "iat": now,
        "exp": now + timedelta(minutes=10),
    }
    payload = {**base_payload, **payload_overrides}
    for claim in drop:
        payload.pop(claim)
    return jwt.encode(payload, secret, algorithm=ALGORITHM)

async def assert_rejected(request, connection, message):
    with pytest.raises(HTTPException) as excinfo:
        await verify_jwt(request, connection)

    assert excinfo.value.status_code == 401
    assert excinfo.value.detail["message"] == message

class TestVerifyJWT:
    @pytest.mark.asyncio
    async def test_valid_token(self, monkeypatch):
        monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)
        connection = make_connection({"userjwtissued": datetime.now(timezone.utc)})

        decoded = await verify_jwt(make_request(make_token()), connection)

        assert decoded["sub"] == USER_ID
        assert decoded["username"] == "byron"
        assert decoded["role"] == "ADMIN"
        connection.fetchrow.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_valid_token_when_never_issued_in_db(self, monkeypatch):
        monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)
        connection = make_connection({"userjwtissued": None})

        decoded = await verify_jwt(make_request(make_token()), connection)

        assert decoded["sub"] == USER_ID

    @pytest.mark.asyncio
    async def test_missing_cookie(self):
        connection = make_connection(None)

        await assert_rejected(make_request(None), connection, "Not authenticated")
        connection.fetchrow.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_expired_token(self, monkeypatch):
        monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)
        token = make_token({"exp": datetime.now(timezone.utc) - timedelta(minutes=10)})

        await assert_rejected(make_request(token), make_connection(None), "Token has expired")

    @pytest.mark.asyncio
    async def test_invalid_token(self, monkeypatch):
        monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)

        await assert_rejected(make_request("this.is.not.valid"), make_connection(None), "Invalid token")

    @pytest.mark.asyncio
    async def test_wrong_secret(self, monkeypatch):
        monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)
        token = make_token(secret="wrong-secret")

        await assert_rejected(make_request(token), make_connection(None), "Invalid token")

    @pytest.mark.asyncio
    async def test_token_without_iat_rejected(self, monkeypatch):
        monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)
        connection = make_connection({"userjwtissued": None})

        await assert_rejected(make_request(make_token(drop=("iat",))), connection, "Invalid token")
        connection.fetchrow.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_non_uuid_sub_rejected(self, monkeypatch):
        monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)
        connection = make_connection({"userjwtissued": None})

        await assert_rejected(make_request(make_token({"sub": "123"})), connection, "Invalid token")
        connection.fetchrow.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_deleted_user_rejected(self, monkeypatch):
        monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)

        await assert_rejected(make_request(make_token()), make_connection(None), "Invalid token")

    @pytest.mark.asyncio
    async def test_revoked_token_rejected(self, monkeypatch):
        monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)
        now = datetime.now(timezone.utc)
        old_token = make_token({"iat": now - timedelta(minutes=5)})
        connection = make_connection({"userjwtissued": now})

        await assert_rejected(make_request(old_token), connection, "Invalid token")

    @pytest.mark.asyncio
    async def test_token_within_leeway_accepted(self, monkeypatch):
        monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)
        now = datetime.now(timezone.utc)
        token = make_token({"iat": now - timedelta(seconds=1)})
        connection = make_connection({"userjwtissued": now})

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
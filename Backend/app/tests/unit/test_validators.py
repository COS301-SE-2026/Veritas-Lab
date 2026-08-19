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
from unittest.mock import MagicMock

TEST_SECRET_KEY = "test-secret"
COOKIE_NAME = "JWT_token"

def make_request(token: str | None) -> MagicMock:
    """Build a mock FastAPI Request with the JWT cookie set."""
    request = MagicMock()
    request.cookies = {COOKIE_NAME: token} if token else {}
    return request


def make_token(payload_overrides: dict = {}, secret: str = TEST_SECRET_KEY) -> str:
    base_payload = {
        "sub": "123",
        "username": "byron",
        "role": "ADMIN",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    payload = {**base_payload, **payload_overrides}
    return jwt.encode(payload, secret, algorithm=ALGORITHM)

class TestVerifyJWT:
    def test_valid_token(self, monkeypatch):
        monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)

        token = make_token()
        request = make_request(token)

        decoded = verify_jwt(request)

        assert decoded["sub"] == "123"
        assert decoded["username"] == "byron"
        assert decoded["role"] == "ADMIN"

    def test_missing_cookie(self):
        request = make_request(None)

        with pytest.raises(HTTPException) as excinfo:
            verify_jwt(request)

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail["message"] == "Not authenticated"

    def test_expired_token(self, monkeypatch):
        monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)

        token = make_token({"exp": datetime.now(timezone.utc) - timedelta(minutes=10)})
        request = make_request(token)

        with pytest.raises(HTTPException) as excinfo:
            verify_jwt(request)

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail["message"] == "Token has expired"

    def test_invalid_token(self, monkeypatch):
        monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)

        request = make_request("this.is.not.valid")

        with pytest.raises(HTTPException) as excinfo:
            verify_jwt(request)

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail["message"] == "Invalid token"

    def test_wrong_secret(self, monkeypatch):
        monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)

        token = make_token(secret="wrong-secret")
        request = make_request(token)

        with pytest.raises(HTTPException) as excinfo:
            verify_jwt(request)

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail["message"] == "Invalid token"

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
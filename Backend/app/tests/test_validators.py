from app.auth.auth import (
    validateEmail,
    validatePassword,
    verifyJWT,
    ALGORITHM
)

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

        decoded = verifyJWT(request)

        assert decoded["sub"] == "123"
        assert decoded["username"] == "byron"
        assert decoded["role"] == "ADMIN"

    def test_missing_cookie(self):
        request = make_request(None)

        with pytest.raises(ValueError, match="Not authenticated"):
            verifyJWT(request)

    def test_expired_token(self, monkeypatch):
        monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)

        token = make_token({"exp": datetime.now(timezone.utc) - timedelta(minutes=10)})
        request = make_request(token)

        with pytest.raises(ValueError, match="Token has expired"):
            verifyJWT(request)

    def test_invalid_token(self, monkeypatch):
        monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)

        request = make_request("this.is.not.valid")

        with pytest.raises(ValueError, match="Invalid token"):
            verifyJWT(request)

    def test_wrong_secret(self, monkeypatch):
        monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)

        token = make_token(secret="wrong-secret")
        request = make_request(token)

        with pytest.raises(ValueError, match="Invalid token"):
            verifyJWT(request)

class TestValidateEmail:
    def test_valid_email(self):
        assert validateEmail("u12345678@tuks.co.za") is True

    def test_invalid_email(self):
        assert validateEmail("hello world") is False

    def test_empty_email(self):
        assert validateEmail("") is False

    def test_email_trimming(self):
        assert validateEmail("  u12345678@tuks.co.za  ") is True

    def test_none_email(self):
        assert validateEmail(None) is False

    def test_missing_at_symbol(self):
        assert validateEmail("userexample.com") is False

    def test_missing_domain(self):
        assert validateEmail("user@") is False

    def test_missing_tld(self):
        assert validateEmail("user@example") is False

class TestValidatePassword:
    def test_valid_password(self):
        assert validatePassword("ThisIsAStrongPassword123@@") is True

    def test_missing_special_char(self):
        assert validatePassword("ThisIsAStrongPassword123") is False

    def test_too_short(self):
        assert validatePassword("Strong1@") is False

    def test_missing_number(self):
        assert validatePassword("@QWertyuipsjdnasndoajd&&saweqwdsadsadffd") is False

    def test_missing_uppercase(self):
        assert validatePassword("qwertyuiopasddf123455!@#$sasd") is False

    def test_missing_lowercase(self):
        assert validatePassword("QUYGYUGUIHUIGYUGUIHUIHI12345321!##@#$") is False

    def test_empty_password(self):
        assert validatePassword("") is False

    def test_none_password(self):
        assert validatePassword(None) is False
from app.auth.auth import (
    validateEmail,
    validatePassword,
    verifyJWT,
    SECRET_KEY,
    ALGORITHM
)

import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt

TEST_SECRET_KEY="test-secret"

def testVerifyJWTValidToken(monkeypatch):
    monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)

    payload = {
        "sub": "123",
        "userId": "123",
        "username": "byron",
        "role": "ADMIN",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10)
    }

    token = jwt.encode(payload, TEST_SECRET_KEY, algorithm=ALGORITHM)

    authorizationHeader = f"Bearer {token}"

    decoded = verifyJWT(authorizationHeader)

    assert decoded["sub"] == "123"
    assert decoded["userId"] == "123"
    assert decoded["username"] == "byron"
    assert decoded["role"] == "ADMIN"


def testVerifyJWTMissingHeader():
    with pytest.raises(ValueError, match="Missing Authorization header"):
        verifyJWT(None)


def testVerifyJWTEmptyHeader():
    with pytest.raises(ValueError, match="Missing Authorization header"):
        verifyJWT("")


def testVerifyJWTInvalidHeaderFormat():
    with pytest.raises(ValueError, match="Invalid Authorization header format"):
        verifyJWT("Token abc123")


def testVerifyJWTMissingToken():
    with pytest.raises(ValueError, match="Missing JWT token"):
        verifyJWT("Bearer ")


def testVerifyJWTExpiredToken(monkeypatch):
    monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)

    payload = {
        "sub": "123",
        "userId": "123",
        "username": "byron",
        "role": "ADMIN",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=10)
    }

    token = jwt.encode(payload, TEST_SECRET_KEY, algorithm=ALGORITHM)

    authorizationHeader = f"Bearer {token}"

    with pytest.raises(ValueError, match="Token has expired"):
        verifyJWT(authorizationHeader)


def testVerifyJWTInvalidToken(monkeypatch):
    monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)

    with pytest.raises(ValueError, match="Invalid token"):
        verifyJWT("Bearer this.is.not.valid")


def testVerifyJWTWrongSecret(monkeypatch):
    monkeypatch.setattr("app.auth.auth.SECRET_KEY", TEST_SECRET_KEY)

    payload = {
        "sub": "123",
        "userId": "123",
        "username": "byron",
        "role": "ADMIN",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10)
    }

    token = jwt.encode(payload, "wrong-secret", algorithm=ALGORITHM)

    authorizationHeader = f"Bearer {token}"

    with pytest.raises(ValueError, match="Invalid token"):
        verifyJWT(authorizationHeader)

def testValidEmail():
    assert validateEmail("u12345678@tuks.co.za") is True

def testInvalidEmail():
    assert validateEmail("hello world") is False

def testEmptyEmail():
    assert validateEmail("") is False

def testEmailTrimming():
    assert validateEmail("  u12345678@tuks.co.za  ") is True

def testPasswordMissingSpecial():
    assert validatePassword("ThisIsAStrongPassword123") is False

def testPasswordLength():
    assert validatePassword("Strong1@") is False

def testPasswordNumber():
    assert validatePassword("@QWertyuipsjdnasndoajd&&saweqwdsadsadffd") is False

def testPasswordUpperCase():
    assert validatePassword("qwertyuiopasddf123455!@#$sasd") is False

def testPasswordLowerCase():
    assert validatePassword("QUYGYUGUIHUIGYUGUIHUIHI12345321!##@#$") is False

def testPasswordMissing():
    assert validatePassword("") is False

def testValidPassword():
    assert validatePassword("ThisIsAStrongPassword123@@") is True


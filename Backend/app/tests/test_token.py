from fastapi.testclient import TestClient
from app.api.main import app
import app.auth.auth as auth
from datetime import datetime, timezone, timedelta

COOKIE_NAME = auth.COOKIE_NAME

def make_client(token: str | None = None) -> TestClient:
    """Create a TestClient with an optional cookie pre-set."""
    c = TestClient(app)
    if token is not None:
        c.cookies.set(COOKIE_NAME, token)
    return c

def test_refresh_token_missing_cookie():
    response = make_client().post("/api/refreshToken")

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Not authenticated"
    }

def test_refresh_token_invalid_jwt(monkeypatch):
    monkeypatch.setattr(auth.jwt, "decode", lambda *args, **kwargs: (_ for _ in ()).throw(auth.JWTError()))
    response = make_client("invalid-token").post("/api/refreshToken")

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Invalid token"
    }
    assert auth.COOKIE_NAME not in response.cookies

def test_refresh_token_does_not_need_refreshing(monkeypatch):
    def mock_jwt_decode(token, secret_key, algorithms, options=None):
        return {
            "sub": "mock-user-id",
            "username": "test_user",
            "role": "INVESTIGATOR",
            "exp": (datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()
        }
    
    monkeypatch.setattr(auth.jwt, "decode", mock_jwt_decode)

    response = make_client("valid-token").post("/api/refreshToken")

    assert response.status_code == 200
    assert response.json() == {
        "status":"success",
        "message":"Token does not need refreshing"
    }
    assert auth.COOKIE_NAME not in response.cookies

def test_refresh_token_success_within_one_minute(monkeypatch):
    def mock_jwt_decode(token, secret_key, algorithms, options=None):
        return {
            "sub": "mock-user-id",
            "username": "test_user",
            "role" : "INVESTIGATOR",
            "exp": (datetime.now(timezone.utc) + timedelta(seconds=30)).timestamp()
        }
    
    def mock_create_token(user):
        assert user == {
            "id": "mock-user-id",
            "username": "test_user",
            "role": "INVESTIGATOR"
        }
        return "new-mock-token"
    
    async def mock_update_user_jwt_issued_via_user(user):
        assert user == {
            "id": "mock-user-id",
            "username": "test_user",
            "role": "INVESTIGATOR"
        }
    
    monkeypatch.setattr(auth.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth, "create_token", mock_create_token)
    monkeypatch.setattr(auth, "update_user_jwt_issued_via_user", mock_update_user_jwt_issued_via_user)

    response = make_client("almost-expired-token").post("/api/refreshToken")

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Token refreshed",
    }

    assert auth.COOKIE_NAME in response.cookies
    assert response.cookies.get(auth.COOKIE_NAME) == "new-mock-token"

def test_refresh_token_success_when_expired(monkeypatch):
    decode_call_count = {"count": 0}

    def mock_jwt_decode(token, secret_key, algorithms, options=None):
        decode_call_count["count"] += 1
        if decode_call_count["count"] == 1:
            raise auth.ExpiredSignatureError()
        return {
            "sub": "mock-user-id",
            "username": "test_user",
            "role": "INVESTIGATOR",
            "exp": (datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp()
        }
    
    def mock_create_token(user):
        assert user == {
            "id": "mock-user-id",
            "username": "test_user",
            "role": "INVESTIGATOR"
        }
        return "new-token-from-expired-token"
    
    async def mock_update_user_jwt_issued_via_user(user):
        assert user == {
            "id": "mock-user-id",
            "username": "test_user",
            "role" : "INVESTIGATOR"
        }

    monkeypatch.setattr(auth.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth, "create_token", mock_create_token)
    monkeypatch.setattr(auth, "update_user_jwt_issued_via_user", mock_update_user_jwt_issued_via_user)

    response = make_client("expired-token").post("/api/refreshToken")

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Token refreshed",
    }
    assert decode_call_count["count"] == 2
    assert auth.COOKIE_NAME in response.cookies
    assert response.cookies.get(auth.COOKIE_NAME) == "new-token-from-expired-token"

def test_refresh_token_expired_but_invalid_on_second_decode(monkeypatch):
    decode_call_count = {"count": 0}

    def mock_jwt_decode(token, secret_key, algorithms, options=None):
        decode_call_count["count"] += 1
        if decode_call_count["count"] == 1:
            raise auth.ExpiredSignatureError()
        raise auth.JWTError()
    
    monkeypatch.setattr(auth.jwt, "decode", mock_jwt_decode)

    response = make_client("expired-but-invalid-token").post("/api/refreshToken")

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Invalid token"
    }
    assert decode_call_count["count"] == 2
    assert auth.COOKIE_NAME not in response.cookies

def test_refresh_token_missing_expiry(monkeypatch):
    def mock_jwt_decode(token, secret_key, algorithms, options=None):
        return {
            "sub": "mock-user-id",
            "username": "test_user",
            "role": "INVESTIGATOR"
        }
    
    monkeypatch.setattr(auth.jwt, "decode", mock_jwt_decode)

    response = make_client("token-missing-expiry").post("/api/refreshToken")

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Token missing expiry"
    }
    assert auth.COOKIE_NAME not in response.cookies

def test_refresh_token_missing_required_fields(monkeypatch):
    def mock_jwt_decode(token, secret_key, algorithms, options=None):
        return {
            "sub": "mock-user-id",
            "exp": (datetime.now(timezone.utc) + timedelta(seconds=30)).timestamp()
        }
    
    monkeypatch.setattr(auth.jwt, "decode", mock_jwt_decode)

    response = make_client("token-missing-fields").post("/api/refreshToken")

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Token missing required fields"
    }
    assert auth.COOKIE_NAME not in response.cookies

def test_refresh_token_update_jwt_issued_fails(monkeypatch):
    def mock_jwt_decode(token, secret_key, algorithms, options=None):
        return {
            "sub": "mock-user-id",
            "username": "test_user",
            "role": "INVESTIGATOR",
            "exp": (datetime.now(timezone.utc) + timedelta(seconds=30)).timestamp()
        }
    
    def mock_create_token(user):
        return "new-mock-token"
    
    async def mock_update_user_jwt_issued_via_user(user):
        raise Exception("Database error")

    monkeypatch.setattr(auth.jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(auth, "create_token", mock_create_token)
    monkeypatch.setattr(auth, "update_user_jwt_issued_via_user", mock_update_user_jwt_issued_via_user)

    response = make_client("almost-expired-token").post("/api/refreshToken")

    assert response.status_code == 500
    assert response.json() == {
        "status": "error",
        "message": "Failed to update token issue time"
    }
    assert auth.COOKIE_NAME not in response.cookies
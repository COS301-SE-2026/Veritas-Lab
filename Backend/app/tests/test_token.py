from fastapi.testclient import TestClient
from app.api.main import app
import app.auth.auth as auth
from datetime import datetime, timezone, timedelta

client = TestClient(app)

def test_refresh_token_missing_authorization():
    response = client.post("/api/refreshToken")

    assert response.status_code == 401
    assert response.json() == {
        "status":"error",
        "message": "Missing Authorization header"
    }

def test_refresh_token_missing_jwt():
    response = client.post(
        "/api/refreshToken",
        headers={"Authorization": "Bearer "}
    )

    assert response.status_code == 401
    assert response.json() == {
        "status":"error",
        "message":"Missing JWT token"
    }

def test_refresh_token_invalid_jwt():
    response = client.post(
        "/api/refreshToken",
        headers={"Authorization": "Bearer invalid-token"}
    )

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Invalid token"
    }

def test_refresh_token_invalid_authorization_format():
    response = client.post(
        "/api/refreshToken",
        headers={"Authorization": "invalid-token"}
    )

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Invalid Authorization header format"
    }

def test_refresh_token_does_not_need_refreshing(monkeypatch):
    def mock_jwt_decode(token, secret_key, algorithms, options=None):
        return {
            "sub": "mock-user-id",
            "username": "test_user",
            "role": "INVESTIGATOR",
            "exp": (datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()
        }
    
    monkeypatch.setattr(auth.jwt, "decode", mock_jwt_decode)

    response = client.post(
        "/api/refreshToken",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "status":"success",
        "message":"Token does not need refreshing"
    }

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
    monkeypatch.setattr(auth, "createToken", mock_create_token)
    monkeypatch.setattr(
        auth,
        "update_user_jwt_issued_via_user",
        mock_update_user_jwt_issued_via_user
    )

    response = client.post(
        "/api/refreshToken",
        headers={"Authorization": "Bearer almost-expired-token"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Token refreshed",
        "token" : "new-mock-token"
    }

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
    monkeypatch.setattr(auth, "createToken", mock_create_token)
    monkeypatch.setattr(
        auth,
        "update_user_jwt_issued_via_user",
        mock_update_user_jwt_issued_via_user
    )

    response = client.post(
        "/api/refreshToken",
        headers={"Authorization": "Bearer expired-token"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Token refreshed",
        "token": "new-token-from-expired-token"
    }

    assert decode_call_count["count"] == 2

def test_refresh_token_expired_but_invalid_on_second_decode(monkeypatch):
    decode_call_count = {"count": 0}

    def mock_jwt_decode(token, secret_key, algorithms, options=None):
        decode_call_count["count"] += 1

        if decode_call_count["count"] == 1:
            raise auth.ExpiredSignatureError()

        raise auth.JWTError()
    
    monkeypatch.setattr(auth.jwt, "decode", mock_jwt_decode)

    response = client.post(
        "/api/refreshToken",
        headers={"Authorization": "Bearer expired-but-invalid-token"}
    )

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Invalid token"
    }

    assert decode_call_count["count"] == 2

def test_refresh_token_missing_expiry(monkeypatch):
    def mock_jwt_decode(token, secret_key, algorithms, options=None):
        return {
            "sub": "mock-user-id",
            "username": "test_user",
            "role": "INVESTIGATOR"
        }
    
    monkeypatch.setattr(auth.jwt, "decode", mock_jwt_decode)

    response = client.post(
        "/api/refreshToken",
        headers={"Authorization": "Bearer token-without-expiry"}
    )

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Token missing expiry"
    }

def test_refresh_token_missing_required_fields(monkeypatch):
    def mock_jwt_decode(token, secret_key, algorithms, options=None):
        return {
            "sub": "mock-user-id",
            "exp": (datetime.now(timezone.utc) + timedelta(seconds=30)).timestamp()
        }
    
    monkeypatch.setattr(auth.jwt, "decode", mock_jwt_decode)

    response = client.post(
        "/api/refreshToken",
        headers={"Authorization": "Bearer token-missing-fields"}
    )

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Token missing required fields"
    }

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
    monkeypatch.setattr(auth, "createToken", mock_create_token)
    monkeypatch.setattr(
        auth,
        "update_user_jwt_issued_via_user",
        mock_update_user_jwt_issued_via_user
    )

    response = client.post(
        "/api/refreshToken",
        headers={"Authorization": "Bearer almost-expired-token"}
    )

    assert response.status_code == 500
    assert response.json() == {
        "status": "error",
        "message": "Failed to update token issue time"
    }

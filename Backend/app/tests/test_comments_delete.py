from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
import asyncpg
from app.api.main import app
import app.api.routers.cases_router as cases_router

client = TestClient(app)

class MockConnectionSuccess:
    def __init__(self):
        self.fetchrow = AsyncMock(return_value={"commentid": 5})
        self.close = AsyncMock()

class MockConnectionNoRow:
    def __init__(self):
        self.fetchrow = AsyncMock(return_value=None)
        self.close = AsyncMock()

class MockConnectionDatabaseError:
    def __init__(self):
        self.close = AsyncMock()

    async def fetchrow(self,*args, **kwargs):
        raise asyncpg.PostgresError("Database error")

async def mock_connect_success(*args, **kwargs):
    return MockConnectionSuccess()

async def mock_connect_no_row(*args, **kwargs):
    return MockConnectionNoRow()

async def mock_connect_database_error(*args, **kwargs):
    return MockConnectionDatabaseError()

def test_delete_comment_success(monkeypatch):
    client.cookies.clear()

    def mock_verifyJWT(request):
        return {
            "sub": "user-id",
            "username": "Normal User",
            "role": "USER"
        }
    
    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.asyncpg, "connect", mock_connect_success)

    response = client.delete("/api/deleteComment/comment/5")

    assert response.status_code == 200
    assert response.json() == {
        "status":"success",
        "message": "Comment deleted successfully."
    }

def test_delete_comment_invalid_jwt(monkeypatch):
    client.cookies.clear()

    def mock_verifyJWT(request):
        raise ValueError("Invalid token")
    
    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.delete("/api/deleteComment/comment/5")

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Invalid token"
    }

def test_delete_comment_missing_jwt_cookie(monkeypatch):
    client.cookies.clear()

    def mock_verifyJWT(request):
        raise ValueError("Missing authentication cookie")
    
    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.delete("/api/deleteComment/comment/5")

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Missing authentication cookie"
    }

def test_delete_comment_not_found(monkeypatch):
    client.cookies.clear()

    def mock_verifyJWT(request):
        return {
            "sub": "user-id",
            "username": "Normal User",
            "role": "USER"
        }
    
    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.asyncpg, "connect", mock_connect_no_row)

    response = client.delete("/api/deleteComment/comment/999")

    assert response.status_code == 404
    assert response.json() == {
        "status": "error",
        "message": "Comment not found or user unauthorized"
    }

def test_delete_comment_unauthorized_user(monkeypatch):
    client.cookies.clear()

    def mock_verifyJWT(request):
        return {
            "sub": "other-user-id",
            "username": "Different User",
            "role": "USER"
        }
    
    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.asyncpg, "connect", mock_connect_no_row)

    response = client.delete("/api/deleteComment/comment/5")

    assert response.status_code == 404
    assert response.json() == {
        "status": "error",
        "message": "Comment not found or user unauthorized"
    }

def test_delete_comment_database_error(monkeypatch):
    client.cookies.clear()

    def mock_verifyJWT(request):
        return {
            "sub": "user-id",
            "username": "Normal User",
            "role": "USER"
        }

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.asyncpg, "connect", mock_connect_database_error)

    response = client.delete("/api/deleteComment/comment/5")

    assert response.status_code == 500
    assert response.json() == {
        "status": "error",
        "message": "Database error"
    }

def test_delete_comment_invalid_comment_id_type(monkeypatch):
    client.cookies.clear()

    response = client.delete("/api/deleteComment/comment/not-an-int")

    assert response.status_code == 422

def test_delete_comment_uses_comment_id_and_username(monkeypatch):
    client.cookies.clear()

    mock_connection = MockConnectionSuccess()
    async def mock_connect_same_connection(*args, **kwargs):
        return mock_connection
    
    def mock_verifyJWT(request):
        return {
            "sub": "user-id",
            "username": "Normal User",
            "role": "USER"
        }
    
    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.asyncpg, "connect", mock_connect_same_connection)

    response = client.delete("/api/deleteComment/comment/5")

    assert response.status_code == 200

    fetchrow_args = mock_connection.fetchrow.call_args[0]

    assert "DELETE FROM" in fetchrow_args[0]
    assert '"Cases_DB"."Comments"' in fetchrow_args[0]
    assert "commentid = $1" in fetchrow_args[0]
    assert "username = $2" in fetchrow_args[0]
    assert "RETURNING commentid" in fetchrow_args[0]

    assert fetchrow_args[1] == 5
    assert fetchrow_args[2] == "Normal User"


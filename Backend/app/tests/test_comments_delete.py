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

async def mock_connect_no_rows(*args, **kwargs):
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



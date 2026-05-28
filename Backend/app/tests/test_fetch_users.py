import pytest
from fastapi.testclient import TestClient

from app.api.main import app
import app.auth.auth as auth

client = TestClient(app)

class MockConnection:
    async def fetch(self, query):
        return [
            {
                "userid": "11111111-1111-1111-1111-111111111111",
                "username": "Admin User",
                "userrole": "ADMIN"
            },
            {
                "userid": "22222222-2222-2222-2222-222222222222",
                "username": "Normal User",
                "userrole":"USER"
            }
        ]
    
    async def close(self):
        pass

@pytest.mark.asyncio
async def mock_connect(*args, **kwargs):
    return MockConnection()

def testFetchUsersSuccess(monkeypatch):
    def mockVerifyJWT(authorization):
        return{
            "userId": "admin-id",
            "username":"Admin user",
            "role": "ADMIN"
        }
    
    monkeypatch.setattr(auth, "verifyJWT", mockVerifyJWT)
    monkeypatch.setattr(auth.asyncpg, "connect", mock_connect)

    response =client.post(
        "/api/fetchUsers",
        json={},
        headers={
            "Authorization": "Bearer valid-token"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "users" in data
    assert len(data["users"]) == 2

    assert data["users"][0] == {
        "id": "11111111-1111-1111-1111-111111111111",
        "username": "Admin User",
        "role": "ADMIN"
    }

    assert data["users"][1] == {
        "id": "22222222-2222-2222-2222-222222222222",
        "username": "Normal User",
        "role":"USER"
    }

def testFetchUsersNotAdmin(monkeypatch):
    def mockVerifyJWT(authorization):
        return{
            "userId": "normal-user-id",
            "username": "Normal User",
            "role": "USER"
        }
    
    monkeypatch.setattr(auth, "verifyJWT", mockVerifyJWT)

    response = client.post(
        "/api/fetchUsers",
        json={},
        headers={
            "Authorization" : "Bearer valid-user-token"
        }
    )

    assert response.status_code == 403

    data = response.json()

    assert data == {
        "status": "error",
        "message": "User unauthorized"
    }
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

def test_fetch_users_success(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt(request):
        return{
            "sub": "admin-id",
            "username":"Admin user",
            "role": "ADMIN"
        }
    
    monkeypatch.setattr(
        auth, 
        "verify_jwt", 
        mock_verify_jwt
    )
    monkeypatch.setattr(
        auth.asyncpg, 
        "connect", 
        mock_connect
    )

    response =client.post(
        "/api/fetchUsers",
        json={}
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

def test_fetch_users_not_admin(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt(request):
        return{
            "sub": "normal-user-id",
            "username": "Normal User",
            "role": "USER"
        }
    
    monkeypatch.setattr(
        auth, 
        "verify_jwt", 
        mock_verify_jwt
    )

    response = client.post(
        "/api/fetchUsers",
        json={}
    )

    assert response.status_code == 403

    data = response.json()

    assert data == {
        "status": "error",
        "message": "User unauthorized"
    }

def test_fetch_users_invalid_token(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt(request):
        raise ValueError("Invalid token")
    
    monkeypatch.setattr(
        auth, 
        "verify_jwt", 
        mock_verify_jwt
    )

    response = client.post(
        "/api/fetchUsers",
        json={}
    )

    assert response.status_code  == 401

    data=response.json()

    assert data == {
        "status":"error",
        "message": "Invalid token" 
    }

def test_fetch_users_no_users(monkeypatch):
    client.cookies.clear()
    class EmptyMockConnection:
        async def fetch(self, query):
            return []
        
        async def close(self):
            pass

    async def empty_mock_connect(*args, **kwargs):
        return EmptyMockConnection()
    
    def mock_verify_jwt(request):
        return{
            "sub":"admin-id",
            "username": "Admin User",
            "role": "ADMIN"
        }
    
    monkeypatch.setattr(
        auth, 
        "verify_jwt", 
        mock_verify_jwt
    )
    monkeypatch.setattr(
        auth.asyncpg, 
        "connect", 
        empty_mock_connect
    )

    response = client.post(
        "/api/fetchUsers",
        json={}
    )

    assert response.status_code == 200

    data = response.json()

    assert data == {
        "status": "success",
        "users":[]
    }

def test_change_user_role_success(monkeypatch):
    client.cookies.clear()
    class MockConnection:
        async def execute(self, query, *args):
            return "UPDATE 1"
        
        async def close(self):
            pass

    async def mock_connect(*args, **kwargs):
        return MockConnection()
    
    def mock_verify_jwt(request):
        return {
            "sub": "admin-id",
            "username": "Admin User",
            "role": "ADMIN"
        }
    
    monkeypatch.setattr(
        auth, 
        "verify_jwt", 
        mock_verify_jwt
    )
    monkeypatch.setattr(
        auth.asyncpg, 
        "connect", 
        mock_connect
    )

    response = client.post(
        "/api/changeUserRole",
        json={
            "userId": "22222222-2222-2222-2222-222222222222",
            "NewRole": "INVESTIGATOR"
        }
    )

    assert response.status_code == 200
    
    data = response.json()
    
    assert data == {
        "status": "success",
        "message": "User role updated to INVESTIGATOR successfully"
    }

def test_change_user_role_not_admin(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt(request):
        return{
            "sub": "normal-user-id",
            "username": "Normal User",
            "role": "USER"
        }
    
    monkeypatch.setattr(
        auth, 
        "verify_jwt", 
        mock_verify_jwt
    )

    response = client.post(
        "/api/changeUserRole",
        json={}
    )

    assert response.status_code == 403

    data = response.json()

    assert data == {
        "status": "error",
        "message": "User unauthorized"
    }

def test_change_user_role_no_user(monkeypatch):
    client.cookies.clear()
    class MockConnection:
        async def execute(self, query, *args):
            return "UPDATE 0"
        
        async def close(self):
            pass

    async def mock_connect(*args, **kwargs):
        return MockConnection()
    
    def mock_verify_jwt(request):
        return {
            "sub": "admin-id",
            "username": "Admin User",
            "role": "ADMIN"
        }
    
    monkeypatch.setattr(
        auth, 
        "verify_jwt", 
        mock_verify_jwt
    )
    monkeypatch.setattr(
        auth.asyncpg, 
        "connect", 
        mock_connect
    )

    response = client.post(
        "/api/changeUserRole",
        json={
            "userId": "12345678-abcd-ef01-2345-6789abcdef01",
            "NewRole": "INVESTIGATOR"
        }
    )

    assert response.status_code == 404
    
    data = response.json()
    
    assert data == {
        "status": "error",
        "message": "No user found with the provided user ID"
    }

def test_change_user_role_invalid_role(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt(request):
        return {
            "sub": "admin-id",
            "username": "Admin User",
            "role": "ADMIN"
        }
    
    monkeypatch.setattr(
        auth, 
        "verify_jwt", 
        mock_verify_jwt
    )

    response = client.post(
        "/api/changeUserRole",
        json={
            "userId": "22222222-2222-2222-2222-222222222222",
            "NewRole": "Monkey"
        }
    )

    assert response.status_code == 400
    
    data = response.json()
    
    assert data == {
        "status": "error",
        "message": "Invalid or missing NewRole field."
    }

def test_admin_cannot_change_self(monkeypatch):
    """Test that the admin cannot change their own role"""
    client.cookies.clear()
    class MockConnection:
        async def execute(self, query, *args):
            return "UPDATE 1"
        
        async def close(self):
            pass

    async def mock_connect(*args, **kwargs):
        return MockConnection()
    
    admin_id = "11111111-1111-1111-1111-111111111111"
    
    def mock_verify_jwt(request):
        return {
            "sub": admin_id,
            "username": "Admin User",
            "role": "ADMIN"
        }
    
    monkeypatch.setattr(
        auth, 
        "verify_jwt", 
        mock_verify_jwt
    )
    monkeypatch.setattr(
        auth.asyncpg, 
        "connect", 
        mock_connect
    )

    response = client.post(
        "/api/changeUserRole",
        json={
            "userId": admin_id,
            "NewRole": "USER"
        }
    )

    assert response.status_code == 403
    
    data = response.json()
    
    assert data == {
        "status": "error",
        "message": "Not allowed to change own role"
    }
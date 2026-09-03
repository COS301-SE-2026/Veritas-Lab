import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.api.main import app
import app.auth.auth as auth
from app.auth.auth import hash_password
from app.core.database import get_connection
from app.tests.unit.database_override import unit_get_connection
client = TestClient(app)
@pytest.fixture(autouse=True)
def override_database_dependency():
    app.dependency_overrides[get_connection] = unit_get_connection
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_connection, None)

CURRENT_PASSWORD = "StrongP@ssword12334567"
NEW_PASSWORD = "NewStrongP@ssword2026!"
@pytest.mark.asyncio
async def test_change_password_success(monkeypatch):
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
            "sub": "mock-user-id",
            "username": "Test User",
            "role": "USER"
        }

    async def mock_search_users_via_username(username, connection):
        return {
            "id": "mock-user-id",
            "email": "u12345678@tuks.co.za",
            "username": "Test User",
            "role": "USER",
            "password": hash_password(CURRENT_PASSWORD)
        }

    monkeypatch.setattr(
        auth,
        "verify_jwt",
        mock_verify_jwt
    )
    monkeypatch.setattr(
        auth,
        "search_users_via_username",
        mock_search_users_via_username
    )
    monkeypatch.setattr(
        auth.asyncpg,
        "connect",
        mock_connect
    )
    response = client.post(
        "/api/changePassword",
        json={
            "currentPassword": CURRENT_PASSWORD,
            "newPassword": NEW_PASSWORD
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data == {
        "status": "success",
        "message": "Password changed successfully"
    }

@pytest.mark.asyncio
async def test_change_password_missing_current_password(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt(request):
        return {
            "sub": "mock-user-id",
            "username": "Test User",
            "role": "USER"
        }
    monkeypatch.setattr(
        auth,
        "verify_jwt",
        mock_verify_jwt
    )
    response = client.post(
        "/api/changePassword",
        json={
            "newPassword": NEW_PASSWORD
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert data == {
        "detail": {
            "status": "error",
            "message": "Missing currentPassword or newPassword field."
        }
    }

@pytest.mark.asyncio
async def test_change_password_missing_new_password(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt(request):
        return {
            "sub": "mock-user-id",
            "username": "Test User",
            "role": "USER"
        }
    monkeypatch.setattr(
        auth,
        "verify_jwt",
        mock_verify_jwt
    )
    response = client.post(
        "/api/changePassword",
        json={
            "currentPassword": CURRENT_PASSWORD
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert data == {
        "detail": {
            "status": "error",
            "message": "Missing currentPassword or newPassword field."
        }
    }

@pytest.mark.asyncio
async def test_change_password_invalid_new_password(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt(request):
        return {
            "sub": "mock-user-id",
            "username": "Test User",
            "role": "USER"
        }
    monkeypatch.setattr(
        auth,
        "verify_jwt",
        mock_verify_jwt
    )
    response = client.post(
        "/api/changePassword",
        json={
            "currentPassword": CURRENT_PASSWORD,
            "newPassword": "weak"
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert data == {
        "detail": {
            "status": "error",
            "message": "Invalid or missing new password. Password must be atleast 12 characters, have an upper and lower case char and a special character"
        }
    }

@pytest.mark.asyncio
async def test_change_password_incorrect_current_password(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt(request):
        return {
            "sub": "mock-user-id",
            "username": "Test User",
            "role": "USER"
        }
    async def mock_search_users_via_username(username, connection):
        return {
            "id": "mock-user-id",
            "email": "u12345678@tuks.co.za",
            "username": "Test User",
            "role": "USER",
            "password": hash_password(CURRENT_PASSWORD)
        }
    monkeypatch.setattr(
        auth,
        "verify_jwt",
        mock_verify_jwt
    )
    monkeypatch.setattr(
        auth,
        "search_users_via_username",
        mock_search_users_via_username
    )
    response = client.post(
        "/api/changePassword",
        json={
            "currentPassword": "WrongCurrentP@ssword123",
            "newPassword": NEW_PASSWORD
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert data == {
        "detail": {
            "status": "error",
            "message": "Current password is incorrect."
        }
    }

@pytest.mark.asyncio
async def test_change_password_same_as_current(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt(request):
        return {
            "sub": "mock-user-id",
            "username": "Test User",
            "role": "USER"
        }
    async def mock_search_users_via_username(username, connection):
        return {
            "id": "mock-user-id",
            "email": "u12345678@tuks.co.za",
            "username": "Test User",
            "role": "USER",
            "password": hash_password(CURRENT_PASSWORD)
        }
    monkeypatch.setattr(
        auth,
        "verify_jwt",
        mock_verify_jwt
    )
    monkeypatch.setattr(
        auth,
        "search_users_via_username",
        mock_search_users_via_username
    )
    response = client.post(
        "/api/changePassword",
        json={
            "currentPassword": CURRENT_PASSWORD,
            "newPassword": CURRENT_PASSWORD
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert data == {
        "detail": {
            "status": "error",
            "message": "New password must be different from your current password."
        }
    }

@pytest.mark.asyncio
async def test_change_password_user_not_found(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt(request):
        return {
            "sub": "mock-user-id",
            "username": "Ghost User",
            "role": "USER"
        }
    async def mock_search_users_via_username(username, connection):
        return None
 
    monkeypatch.setattr(
        auth,
        "verify_jwt",
        mock_verify_jwt
    )
    monkeypatch.setattr(
        auth,
        "search_users_via_username",
        mock_search_users_via_username
    )
    response = client.post(
        "/api/changePassword",
        json={
            "currentPassword": CURRENT_PASSWORD,
            "newPassword": NEW_PASSWORD
        }
    )
    assert response.status_code == 404
    data = response.json()
    assert data == {
        "detail": {
            "status": "error",
            "message": "No user found for the authenticated account."
        }
    }
    
@pytest.mark.asyncio
async def test_change_password_invalid_token(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt(request):
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error",
                "message": "Invalid token"
            }
        )
    monkeypatch.setattr(
        auth,
        "verify_jwt",
        mock_verify_jwt
    )
    response = client.post(
        "/api/changePassword",
        json={
            "currentPassword": CURRENT_PASSWORD,
            "newPassword": NEW_PASSWORD
        }
    )
    assert response.status_code == 401
    data = response.json()
    assert data == {
        "detail": {
            "status": "error",
            "message": "Invalid token"
        }
    }
    # completed all the above tests while attempting to follow the standards as close as possible
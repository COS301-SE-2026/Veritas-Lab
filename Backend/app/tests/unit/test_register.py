import pytest
from fastapi.testclient import TestClient
from app.api.main import app
import app.auth.auth as auth
from app.core.database import get_connection as database_get_connection
from app.tests.unit.database_override import unit_get_connection

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_database_dependency():
    app.dependency_overrides[database_get_connection] = unit_get_connection
    try:
        yield
    finally:
        app.dependency_overrides.pop(database_get_connection, None)

def test_successful_registration(monkeypatch):
    client.cookies.clear()
    async def mock_search_users_via_email(email, connection):
        return None

    async def mock_search_users_via_username(username, connection):
        return None

    async def mock_insert_user(email, username, role, hashedPassword, connection):
        return {
            "id": "mock-user-id",
            "email": email,
            "username": username,
            "role": role
        }
    
    def mock_create_token(user):
        return "mockedJWTToken"
    
    async def mock_update_user_JWT_issued(email, connection):
        return None

    monkeypatch.setattr(auth, "search_users_via_email", mock_search_users_via_email)
    monkeypatch.setattr(auth, "search_users_via_username", mock_search_users_via_username)
    monkeypatch.setattr(auth, "insert_user", mock_insert_user)
    monkeypatch.setattr(auth, "create_token", mock_create_token)
    monkeypatch.setattr(auth, "update_user_jwt_issued", mock_update_user_JWT_issued)

    response = client.post(
        "/api/register",
        json={
            "email": "analyst@veritas.lab",
            "password": "StrongP@ssword1234",
            "username": "Test Analyst"
        }
    )

    assert response.status_code == 201
    assert response.json() == {
        "status": "success",
        "message": "Account created successfully"
    }

    assert auth.COOKIE_NAME in response.cookies
    assert response.cookies.get(auth.COOKIE_NAME) == "mockedJWTToken"

def test_invalid_email_returns_400():
    client.cookies.clear()
    response = client.post(
        "/api/register",
        json={
            "email": "invalid-email-no-domain",
            "password": "StrongP@ssword1234",
            "username": "Test Analyst"
        }
    )

    assert response.status_code == 400
    assert auth.COOKIE_NAME not in response.cookies

def test_missing_email_returns_400():
    client.cookies.clear()
    response = client.post(
        "/api/register",
        json={
            "email": None,
            "password": "StrongP@ssword1234",
            "username": "Test Analyst"
        }
    )

    assert response.status_code == 400
    assert auth.COOKIE_NAME not in response.cookies

#testing invalid password
def test_invalid_password_returns_400():
    client.cookies.clear()
    response = client.post(
        "/api/register",
        json={
            "email": "analyst@veritas.lab",
            "password": "weak",
            "username": "Test Analyst"
        }
    )

    assert response.status_code == 400
    assert auth.COOKIE_NAME not in response.cookies

def test_missing_password_returns_400():
    client.cookies.clear()
    response = client.post(
        "/api/register",
        json={
            "email": "analyst@veritas.lab",
            "password": None,
            "username": "Test Analyst"
        }
    )

    assert response.status_code == 400
    assert auth.COOKIE_NAME not in response.cookies

#test missing username
def test_missing_username_returns_400():
    client.cookies.clear()
    response = client.post(
        "/api/register",
        json={
            "email": "analyst@veritas.lab",
            "password": "StrongP@ssword1234",
            "username": None
        }
    )

    assert response.status_code == 400
    assert auth.COOKIE_NAME not in response.cookies

def test_duplicate_email_returns_409(monkeypatch):
    client.cookies.clear()
    async def mock_search_users_via_email(email, connection):
        return {
            "id": "existing-id",
            "email": email,
            "username": "Existing User",
            "role": "USER"
        }

    async def mock_search_users_via_username(username, connection):
        return None

    monkeypatch.setattr(
        auth, 
        "search_users_via_email", 
        mock_search_users_via_email
    )
    monkeypatch.setattr(
        auth, 
        "search_users_via_username", 
        mock_search_users_via_username
    )

    response = client.post(
        "/api/register",
        json={
            "email": "analyst@veritas.lab",
            "password": "Makelana@2026_Capstone",
            "username": "Test Dupe_Email"
        }
    )

    assert response.status_code == 409
    assert auth.COOKIE_NAME not in response.cookies

def test_duplicate_username_returns_409(monkeypatch):
    client.cookies.clear()

    async def mock_search_users_via_email(email, connection):
        return None

    async def mock_search_users_via_username(username, connection):
        return{
            "id": "existing-id",
            "email": "someone@veritas.lab",
            "username": username,
            "role": "USER"
        }

    monkeypatch.setattr(
        auth, 
        "search_users_via_email", 
        mock_search_users_via_email
    )
    monkeypatch.setattr(
        auth, 
        "search_users_via_username", 
        mock_search_users_via_username
    )

    response = client.post(
        "api/register",
        json={
            "email": "analyst@veritas.lab",
            "password": "Makelana@2026_Capstone",
            "username": "Taken Username"
        }
    )

    assert response.status_code == 409
    assert auth.COOKIE_NAME not in response.cookies
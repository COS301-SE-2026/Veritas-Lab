import pytest
from fastapi.testclient import TestClient
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

AMBIGUOUS_ERROR= "The email and/or password are invalid"

def test_successful_login(monkeypatch):
    client.cookies.clear()
    
    async def mock_search_users_via_email(email, connection):
        hashed_password= hash_password("StrongP@ssword12334567")
        return {
            "id": "mock-user-id",
            "email": "u12345678@tuks.co.za",
            "username": "Test User",
            "role": "USER",
            "password": hashed_password
        }
    
    def mock_create_token(user):
        return "mockedJWTToken"
    
    async def mock_update_user_jwt_issued(email, connection):
        return None
    
    monkeypatch.setattr(
        auth,
        "search_users_via_email",
        mock_search_users_via_email
    )
    monkeypatch.setattr(
        auth,
        "create_token",
        mock_create_token
    )
    monkeypatch.setattr(
        auth, 
        "update_user_jwt_issued", 
        mock_update_user_jwt_issued
    )

    response = client.post(
        "/api/login",
        json= {
            "email":"u12345678@tuks.co.za",
            "password": "StrongP@ssword12334567"
        }
    )

    assert response.status_code == 200

    assert response.json() =={
        "status":"success",
        "message":"Logged in successfully"
    }

    assert auth.COOKIE_NAME in response.cookies
    assert response.cookies.get(auth.COOKIE_NAME) == "mockedJWTToken"

def test_login_incorrect_password(monkeypatch):
    client.cookies.clear()
    async def mock_search_users_via_email(email, connection):
        hashed_password= hash_password("CorrectP@ssword1234567")
        return {
            "id": "mock-user-id",
            "email": "u12345678@tuks.co.za",
            "username": "Test User",
            "role": "USER",
            "password": hashed_password
        }

    monkeypatch.setattr(
        auth, 
        "search_users_via_email", 
        mock_search_users_via_email
    )

    response = client.post(
        "/api/login",
        json={
            "email": "u12345678@tuks.co.za",
            "password": "WrongP@ssword1234567"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail":{
            "status": "error",
            "message": AMBIGUOUS_ERROR
        }
    }

    assert auth.COOKIE_NAME not in response.cookies

def test_login_user_does_not_exist(monkeypatch):
    client.cookies.clear()
    async def mock_search_users_via_email(email, connection):
        return None

    monkeypatch.setattr(
        auth, 
        "search_users_via_email", 
        mock_search_users_via_email
    )

    response = client.post(
        "/api/login",
        json={
            "email": "missing@user.com",
            "password": "StrongP@ssword12334567"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail":{
            "status": "error",
            "message": AMBIGUOUS_ERROR
        }
    }
    assert auth.COOKIE_NAME not in response.cookies

def test_login_missing_password():
    client.cookies.clear()
    response = client.post(
        "/api/login",
        json={
            "email": "u12345678@tuks.co.za"
        }
    )

    assert response.status_code == 400
    assert auth.COOKIE_NAME not in response.cookies

def test_login_incorrect_email():
    client.cookies.clear()
    response = client.post(
        "/api/login",
        json={
            "email": "not-an-email",
            "password": "StrongP@ssword12334567"
        }
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail":{
            "status": "error",
            "message": "Invalid or missing email field. E.g of a valid email: veritas@lab.com"
        }
    }
    assert auth.COOKIE_NAME not in response.cookies

def test_login_missing_email():
    client.cookies.clear()
    response = client.post(
        "/api/login",
        json={
            "password": "StrongP@ssword12334567"
        }
    )

    assert response.status_code == 400
    assert auth.COOKIE_NAME not in response.cookies

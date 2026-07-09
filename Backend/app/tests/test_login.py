from fastapi.testclient import TestClient
from app.api.main import app
import app.auth.auth as auth
from app.auth.auth import hashPassword

client = TestClient(app)

AMBIGUOUS_ERROR= "A user with either this password or email already exists or it is invalid"

def test_successful_login(monkeypatch):
    client.cookies.clear()
    
    async def mock_searchUsersViaEmail(email):
        hashedPassword= hashPassword("StrongP@ssword12334567")
        return {
            "id": "mock-user-id",
            "email": "u12345678@tuks.co.za",
            "username": "Test User",
            "role": "USER",
            "password": hashedPassword
        }
    
    def mock_createToken(user):
        return "mockedJWTToken"
    
    async def mock_updateUserJWTIssued(email):
        return None
    
    monkeypatch.setattr(auth,"searchUsersViaEmail",mock_searchUsersViaEmail)
    monkeypatch.setattr(auth,"createToken",mock_createToken)
    monkeypatch.setattr(auth, "updateUserJWTIssued", mock_updateUserJWTIssued)

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
    async def mock_searchUsersViaEmail(email):
        hashedPassword = hashPassword("CorrectP@ssword1234567")
        return {
            "id": "mock-user-id",
            "email": "u12345678@tuks.co.za",
            "username": "Test User",
            "role": "USER",
            "password": hashedPassword
        }

    monkeypatch.setattr(auth, "searchUsersViaEmail", mock_searchUsersViaEmail)

    response = client.post(
        "/api/login",
        json={
            "email": "u12345678@tuks.co.za",
            "password": "WrongP@ssword1234567"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": AMBIGUOUS_ERROR
    }

    assert auth.COOKIE_NAME not in response.cookies

def test_login_user_does_not_exist(monkeypatch):
    client.cookies.clear()
    async def mock_searchUsersViaEmail(email):
        return None

    monkeypatch.setattr(auth, "searchUsersViaEmail", mock_searchUsersViaEmail)

    response = client.post(
        "/api/login",
        json={
            "email": "missing@user.com",
            "password": "StrongP@ssword12334567"
        }
    )

    assert response.status_code == 404
    assert response.json() == {
        "status": "error",
        "message": AMBIGUOUS_ERROR
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
        "status": "error",
        "message": "Invalid or missing email field. E.g of a valid email: veritas@lab.com"
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

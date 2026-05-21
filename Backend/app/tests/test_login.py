from fastapi.testclient import TestClient
from app.api.main import app
import app.auth.auth as auth
from app.auth.auth import hashPassword

client = TestClient(app)

def testSuccessfulLogin(monkeypatch):
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
        "token": "mockedJWTToken"
    }

def testLoginIncorrectPassword(monkeypatch):
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
        "message": "Invalid email or password"
    }

def testLoginUserDoesNotExist(monkeypatch):
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
        "message": "A User with this email does not exist. Please register"
    }

def testLoginMissingPassword():
    response = client.post(
        "/api/login",
        json={
            "email": "u12345678@tuks.co.za"
        }
    )

    assert response.status_code == 400


def testLoginIncorrectEmail():
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


def testLoginMissingEmail():
    response = client.post(
        "/api/login",
        json={
            "password": "StrongP@ssword12334567"
        }
    )

    assert response.status_code == 400
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


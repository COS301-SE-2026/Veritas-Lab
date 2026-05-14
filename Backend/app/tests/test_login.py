from fastapi.testclient import TestClient
from app.api.main import app
import app.auth.auth as auth
from app.auth.auth import hashString

client = TestClient(app)

def testSuccessfulLogin(monkeypatch):
    def mock_searchUsersViaEmail(email):
        hashedPassword= hashString("StrongP@ssword12334567")
        return {
            "email":"u12345678@tuks.co.za",
            "password": hashedPassword
        }
    
    def mock_createToken(user):
        return "mockedJWTToken"
    
    monkeypatch.setattr(auth,"searchUsersViaEmail",mock_searchUsersViaEmail)
    monkeypatch.setattr(auth,"createToken",mock_createToken)

    response = client.post(
        "/api/login",
        json= {
            "email":"u12345678@tuks.co.za",
            "password": "StrongP@ssword12334567"
        }
    )

    assert response.status_code == 200

    hashedToken = hashString("mockedJWTToken")

    assert response.json() =={
        "status":"success",
        "token": hashedToken
    }


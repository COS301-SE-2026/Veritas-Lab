from fastapi.testclient import TestClient
from app.api.main import app
import app.auth.auth as auth

client = TestClient(app)

def testSuccessfulRegistration(monkeypatch):
    async def mock_searchUsersViaEmail(email):
        return None  # No existing user so email is free to register

    async def mock_insertUser(email, username, role, hashedPassword):
        return {
            "id": "mock-user-id",
            "email": email,
            "username": username,
            "role": role
        }

    monkeypatch.setattr(auth, "searchUsersViaEmail", mock_searchUsersViaEmail)
    monkeypatch.setattr(auth, "insertUser", mock_insertUser)

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

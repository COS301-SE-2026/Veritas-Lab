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

def testInvalidEmailReturns400():
    response = client.post(
        "/api/register",
        json={
            "email": "invalid-email-no-domain",
            "password": "StrongP@ssword1234",
            "username": "Test Analyst"
        }
    )

    assert response.status_code == 400

def testMissingEmailReturns400():
    response = client.post(
        "/api/register",
        json={
            "email": None,
            "password": "StrongP@ssword1234",
            "username": "Test Analyst"
        }
    )

    assert response.status_code == 400

#testing invalid password
def testInvalidPasswordReturns400():
    response = client.post(
        "/api/register",
        json={
            "email": "analyst@veritas.lab",
            "password": "weak",
            "username": "Test Analyst"
        }
    )

    assert response.status_code == 400

def testMissingPasswordReturns400():
    response = client.post(
        "/api/register",
        json={
            "email": "analyst@veritas.lab",
            "password": None,
            "username": "Test Analyst"
        }
    )

    assert response.status_code == 400

    #test missing username
def testMissingUsernameReturns400():
    response = client.post(
        "/api/register",
        json={
            "email": "analyst@veritas.lab",
            "password": "StrongP@ssword1234",
            "username": None
        }
    )

    assert response.status_code == 400

#testing duplicate email. SO email is already in use or registered
def testDuplicateEmailReturns409(monkeypatch):
    async def mock_searchUsersViaEmail(email):
        return {"id": "existing-id", "email": email, "username": "Existing User", "role": "analyst"}

    monkeypatch.setattr(auth, "searchUsersViaEmail", mock_searchUsersViaEmail)

    response = client.post(
        "/api/register",
        json={
            "email": "analyst@veritas.lab",
            "password": "Makelana@2026_Capstone",
            "username": "Test Dupe_Email"
        }
    )

    assert response.status_code == 409

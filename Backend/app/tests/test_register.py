from fastapi.testclient import TestClient
from app.api.main import app
import app.auth.auth as auth

client = TestClient(app)

def test_successful_registration(monkeypatch):
    client.cookies.clear()
    async def mock_searchUsersViaEmail(email):
        return None

    async def mock_searchUsersViaUsername(username):
        return None

    async def mock_insertUser(email, username, role, hashedPassword):
        return {
            "id": "mock-user-id",
            "email": email,
            "username": username,
            "role": role
        }
    
    def mock_createToken(user):
        return "mockedJWTToken"
    
    async def mock_updateUserJWTIssued(email): 
        return None

    monkeypatch.setattr(auth, "searchUsersViaEmail", mock_searchUsersViaEmail)
    monkeypatch.setattr(auth, "searchUsersViaUsername", mock_searchUsersViaUsername)
    monkeypatch.setattr(auth, "insertUser", mock_insertUser)
    monkeypatch.setattr(auth, "createToken", mock_createToken)
    monkeypatch.setattr(auth, "updateUserJWTIssued", mock_updateUserJWTIssued)

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
    async def mock_searchUsersViaEmail(email):
        return {
            "id": "existing-id",
            "email": email,
            "username": "Existing User",
            "role": "USER"
        }

    async def mock_searchUsersViaUsername(username):
        return None

    monkeypatch.setattr(auth, "searchUsersViaEmail", mock_searchUsersViaEmail)
    monkeypatch.setattr(auth, "searchUsersViaUsername", mock_searchUsersViaUsername)

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

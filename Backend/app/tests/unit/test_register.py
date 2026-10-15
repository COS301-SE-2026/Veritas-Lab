import asyncio

import pytest
from fastapi.testclient import TestClient
from app.api.main import app
import app.auth.auth as auth
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


# register now uses ONE combined lookup instead of search_users_via_email + search_users_via_username
def mock_lookup_returning(exists, calls=None):
    async def mock_user_exists_via_email_or_username(email, username, connection):
        if calls is not None:
            calls.append((email, username))
        return exists

    return mock_user_exists_via_email_or_username


def test_successful_registration(monkeypatch):
    client.cookies.clear()

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

    monkeypatch.setattr(auth, "user_exists_via_email_or_username", mock_lookup_returning(False))
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
    calls = []

    monkeypatch.setattr(auth, "user_exists_via_email_or_username", mock_lookup_returning(True, calls))

    response = client.post(
        "/api/register",
        json={
            "email": "analyst@veritas.lab",
            "password": "Makelana@2026_Capstone",
            "username": "Test Dupe_Email"
        }
    )

    assert response.status_code == 409
    assert response.json()["detail"]["message"] == auth.AMBIGUOUS_ERROR
    assert calls == [("analyst@veritas.lab", "Test Dupe_Email")]
    assert auth.COOKIE_NAME not in response.cookies


def test_duplicate_username_returns_409(monkeypatch):
    client.cookies.clear()
    calls = []

    monkeypatch.setattr(auth, "user_exists_via_email_or_username", mock_lookup_returning(True, calls))

    response = client.post(
        "/api/register",
        json={
            "email": "analyst@veritas.lab",
            "password": "Makelana@2026_Capstone",
            "username": "Taken Username"
        }
    )

    assert response.status_code == 409
    assert response.json()["detail"]["message"] == auth.AMBIGUOUS_ERROR
    assert calls == [("analyst@veritas.lab", "Taken Username")]
    assert auth.COOKIE_NAME not in response.cookies


def test_duplicate_registration_does_not_insert_user(monkeypatch):
    client.cookies.clear()
    insert_calls = []

    async def mock_insert_user(email, username, role, hashedPassword, connection):
        insert_calls.append(email)
        return None

    monkeypatch.setattr(auth, "user_exists_via_email_or_username", mock_lookup_returning(True))
    monkeypatch.setattr(auth, "insert_user", mock_insert_user)

    response = client.post(
        "/api/register",
        json={
            "email": "analyst@veritas.lab",
            "password": "Makelana@2026_Capstone",
            "username": "Taken Username"
        }
    )

    assert response.status_code == 409
    assert insert_calls == []


# ---- changes made to stop the timing leak (account enumeration) ----

def test_register_uses_a_single_lookup(monkeypatch):
    client.cookies.clear()
    calls = []

    async def must_not_be_called(*args, **kwargs):
        raise AssertionError("register should use the combined lookup only")

    monkeypatch.setattr(auth, "user_exists_via_email_or_username", mock_lookup_returning(True, calls))
    monkeypatch.setattr(auth, "search_users_via_email", must_not_be_called)
    monkeypatch.setattr(auth, "search_users_via_username", must_not_be_called)

    response = client.post(
        "/api/register",
        json={
            "email": "analyst@veritas.lab",
            "password": "Makelana@2026_Capstone",
            "username": "Taken Username"
        }
    )

    assert response.status_code == 409
    assert len(calls) == 1


@pytest.mark.parametrize("account_exists", [True, False])
def test_password_is_hashed_whether_or_not_account_exists(monkeypatch, account_exists):
    # hashing before the 409 decision keeps taken and new accounts at the same cost
    client.cookies.clear()
    hash_calls = []
    real_hash_password = auth.hash_password

    def counting_hash_password(password):
        hash_calls.append(password)
        return real_hash_password(password)

    async def mock_insert_user(email, username, role, hashedPassword, connection):
        return {"id": "mock-user-id", "email": email, "username": username, "role": role}

    async def mock_update_user_JWT_issued(email, connection):
        return None

    monkeypatch.setattr(auth, "hash_password", counting_hash_password)
    monkeypatch.setattr(auth, "user_exists_via_email_or_username", mock_lookup_returning(account_exists))
    monkeypatch.setattr(auth, "insert_user", mock_insert_user)
    monkeypatch.setattr(auth, "create_token", lambda user: "mockedJWTToken")
    monkeypatch.setattr(auth, "update_user_jwt_issued", mock_update_user_JWT_issued)

    response = client.post(
        "/api/register",
        json={
            "email": "analyst@veritas.lab",
            "password": "Makelana@2026_Capstone",
            "username": "Test Analyst"
        }
    )

    assert response.status_code == (409 if account_exists else 201)
    assert hash_calls == ["Makelana@2026_Capstone"]


# ---- the new helper itself ----

class FakeConnection:
    def __init__(self, row):
        self.row = row
        self.calls = []

    async def fetchrow(self, query, *args):
        self.calls.append((query, args))
        return self.row


def test_user_exists_returns_true_when_a_row_is_found():
    connection = FakeConnection({"?column?": 1})

    result = asyncio.run(
        auth.user_exists_via_email_or_username("analyst@veritas.lab", "Test Analyst", connection)
    )

    assert result is True


def test_user_exists_returns_false_when_no_row_is_found():
    connection = FakeConnection(None)

    result = asyncio.run(
        auth.user_exists_via_email_or_username("analyst@veritas.lab", "Test Analyst", connection)
    )

    assert result is False


def test_user_exists_makes_one_query_with_both_values():
    connection = FakeConnection(None)

    asyncio.run(
        auth.user_exists_via_email_or_username("analyst@veritas.lab", "Test Analyst", connection)
    )

    assert len(connection.calls) == 1
    query, args = connection.calls[0]
    assert args == ("analyst@veritas.lab", "Test Analyst")
    assert "OR" in query
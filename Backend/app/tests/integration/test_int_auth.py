import pytest
from fastapi.testclient import TestClient
from app.api.main import app
from app.core.env import User_Settings, Postgres_Settings
import asyncpg
from datetime import datetime, timedelta, timezone

USER_SETTINGS=User_Settings()
POSTGRES_SEETTINGS=Postgres_Settings()
AMBIGUOUS_ERROR= "The email and/or password are invalid"

async def get_connection() -> asyncpg.Connection:
    return await asyncpg.connect(
        user=POSTGRES_SEETTINGS.DB_USER,
        password=POSTGRES_SEETTINGS.DB_PASSWORD,
        database=POSTGRES_SEETTINGS.DB_NAME,
        host=POSTGRES_SEETTINGS.DB_HOST,
        port=POSTGRES_SEETTINGS.DB_PORT,
        ssl="require" if POSTGRES_SEETTINGS.DB_SSL else None,
    )

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.mark.asyncio
async def test_integration_user_login_success(client):
    client.post("/api/register")
    payload = {
        "email": USER_SETTINGS.E2E_USER_EMAIL,
        "password": USER_SETTINGS.E2E_USER_PASSWORD
    }
    before_login_time = datetime.now(timezone.utc)

    response = client.post("/api/login", json=payload)

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Logged in successfully"
    connection=await  get_connection()
    try:
        row = await connection.fetchrow(
            """
            SELECT userjwtissued 
            FROM "Users_DB"."Users" 
            WHERE useremail = $1
            """,
            USER_SETTINGS.E2E_USER_EMAIL
        )

        assert row is not None, f"User with email {USER_SETTINGS.E2E_USER_EMAIL} not found in DB"
        jwt_issued_at = row["userjwtissued"]
        assert jwt_issued_at is not None, "No JWT issue db entry"

        if jwt_issued_at.tzinfo is None:
            before_login_time = before_login_time.replace(tzinfo=None)

        assert jwt_issued_at >= (before_login_time - timedelta(seconds=1)), (
            f"userjwtissued timestamp ({jwt_issued_at}) was not updated during this test. "
        )
    finally:
        await connection.close()

async def check_no_jwt_issued(before_login_time):
    connection=await  get_connection()
    try:
        row = await connection.fetchrow(
            """
            SELECT userjwtissued 
            FROM "Users_DB"."Users" 
            WHERE useremail = $1
            """,
            USER_SETTINGS.E2E_USER_EMAIL
        )


        jwt_issued_at = row["userjwtissued"]
        

        assert jwt_issued_at < before_login_time , (
            f"userjwtissued timestamp ({jwt_issued_at}) was updated while testing a failure. "
        )
    finally:
        await connection.close()


@pytest.mark.asyncio
async def test_integration_login_invalid_password_failure(client):
    client.post("/api/register")
    payload = {
        "email": USER_SETTINGS.E2E_USER_EMAIL,
        "password": "Failedp@ssword"
    }
    before_login_time = datetime.now(timezone.utc)

    response = client.post("/api/login", json=payload)

    assert response.status_code == 400

    data = response.json()
    assert data["detail"]["status"] == "error"
    assert data["detail"]["message"] == "Invalid or missing password. Password must be atleast 12 characters, have an upper and lower case char and a special character"
    await check_no_jwt_issued(before_login_time)

@pytest.mark.asyncio
async def test_integration_login_wrong_password_failure(client):
    client.post("/api/register")
    payload = {
        "email": USER_SETTINGS.E2E_USER_EMAIL,
        "password": "Failedp@ssword1246"
    }
    before_login_time = datetime.now(timezone.utc)

    response = client.post("/api/login", json=payload)

    assert response.status_code == 401

    data = response.json()
    assert data["detail"]["status"] == "error"
    assert data["detail"]["message"] == AMBIGUOUS_ERROR
    await check_no_jwt_issued(before_login_time)



@pytest.mark.asyncio
async def test_integration_login_no_email_failure(client):
    client.post("/api/register")
    payload = {
        "email": "",
        "password": USER_SETTINGS.E2E_USER_PASSWORD
    }
    before_login_time = datetime.now(timezone.utc)

    response = client.post("/api/login", json=payload)

    assert response.status_code == 400

    data = response.json()
    assert data["detail"]["status"] == "error"
    assert data["detail"]["message"] == "Invalid or missing email field. E.g of a valid email: veritas@lab.com"
    await check_no_jwt_issued(before_login_time)

@pytest.mark.asyncio
async def test_integration_login_invalid_email_failure(client):
    client.post("/api/register")
    payload = {
        "email": "kleis#to",
        "password": USER_SETTINGS.E2E_USER_PASSWORD
    }
    before_login_time = datetime.now(timezone.utc)

    response = client.post("/api/login", json=payload)

    assert response.status_code == 400

    data = response.json()
    assert data["detail"]["status"] == "error"
    assert data["detail"]["message"] == "Invalid or missing email field. E.g of a valid email: veritas@lab.com"
    connection=await  get_connection()
    try:
        row = await connection.fetchrow(
            """
            SELECT userjwtissued 
            FROM "Users_DB"."Users" 
            WHERE useremail = $1
            """,
            USER_SETTINGS.E2E_USER_EMAIL
        )


        jwt_issued_at = row["userjwtissued"]
        

        assert jwt_issued_at < before_login_time , (
            f"userjwtissued timestamp ({jwt_issued_at}) was updated while testing a failure. "
        )
    finally:
        await connection.close()

@pytest.mark.asyncio
async def test_integration_login_wrong_email_failure(client):
    client.post("/api/register")
    payload = {
        "email": "Pepsi@gmail.com",
        "password": USER_SETTINGS.E2E_USER_PASSWORD
    }
    before_login_time = datetime.now(timezone.utc)

    response = client.post("/api/login", json=payload)

    assert response.status_code == 401

    data = response.json()
    assert data["detail"]["status"] == "error"
    assert data["detail"]["message"] == AMBIGUOUS_ERROR
    await check_no_jwt_issued(before_login_time)

@pytest.mark.asyncio
async def test_integration_register_success(client):
    payload = {
        "email": "integration.register@example.com",
        "username": "integration_user",
        "password": "ValidPassword!123"
    }

    response = client.post("/api/register", json=payload)

    assert response.status_code == 201
    assert response.json() == {
        "status": "success",
        "message": "Account created successfully"
    }

@pytest.mark.asyncio
async def test_integration_register_sets_jwt_cookie(client):
    payload = {
        "email": "cookie.register@example.com",
        "username": "cookie_user",
        "password": "ValidPassword!123"
    }

    response = client.post("/api/register", json=payload)
    assert response.status_code == 201
    assert "JWT_token" in response.cookies
    assert response.cookies.get("JWT_token") is not None

    connection = await get_connection()

    try:
        user = await connection.fetchrow(
            """
            SELECT UserJWTIssued
            FROM "Users_DB"."Users"
            WHERE UserEmail = $1
            """,
            payload["email"]
        )

        assert user is not None
        assert user["userjwtissued"] is not None
    finally:
        await connection.close()


@pytest.mark.asyncio
async def test_integration_register_invalid_email(client):
    payload = {
        "email": "invalid-email",
        "username": "test_user",
        "password": "ValidPassword!123"
    }

    response = client.post("/api/register", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] == "Invalid or missing email field. E.g of a valid email: veritas@lab.com"

@pytest.mark.asyncio
async def test_integration_register_invalid_password(client):
    payload = {
        "email": "valid@example.com",
        "username": "test_user",
        "password": "password"
    }

    response = client.post("/api/register", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] == "Invalid or missing password. Password must be atleast 12 characters, have an upper and lower case char and a special character"

@pytest.mark.asyncio
async def test_integration_register_blank_username(client):
    payload = {
        "email": "blankusername@example.com",
        "username": "   ",
        "password": "ValidPassword!123"
    }

    response = client.post("/api/register", json=payload)

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Invalid or missing username"
        }
    }

@pytest.mark.asyncio
async def test_integration_register_duplicate_email(client):
    first_user = {
        "email": "duplicate@example.com",
        "username": "first_user",
        "password": "ValidPassword!123"
    }

    response = client.post("/api/register", json=first_user)

    assert response.status_code == 201

    second_user = {
        "email": "duplicate@example.com",
        "username": "different_user",
        "password": "ValidPassword!123"
    }

    response = client.post("/api/register", json=second_user)

    assert response.status_code == 409
    assert response.json()["detail"]["status"] == "error"

@pytest.mark.asyncio
async def test_integration_register_duplicate_username(client):
    first_user = {
        "email": "user1@example.com",
        "username": "duplicate_username",
        "password": "ValidPassword!123"
    }

    response = client.post("/api/register", json=first_user)

    assert response.status_code == 201

    second_user = {
        "email": "user2@example.com",
        "username": "duplicate_username",
        "password": "ValidPassword!123"
    }

    response = client.post("/api/register", json=second_user)

    assert response.status_code == 409
    assert response.json()["detail"]["status"] == "error"

@pytest.mark.asyncio
async def test_integration_register_persists_user(client):
    payload = {
        "email": "persisted@example.com",
        "username": "persisted_user",
        "password": "ValidPassword!123"
    }

    response = client.post("/api/register", json=payload)

    assert response.status_code == 201

    connection=await get_connection()
    try:
        user = await connection.fetchrow(
            """
            SELECT UserEmail, UserName, UserRole 
            FROM "Users_DB"."Users" 
            WHERE UserEmail = $1
            """,
            payload["email"]
        )
    
        assert user is not None
        assert user["useremail"] == payload["email"]
        assert user["username"] == payload["username"]
        assert user["userrole"] == "USER"
    finally:
        await connection.close()

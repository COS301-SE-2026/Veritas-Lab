import pytest
from fastapi.testclient import TestClient
from app.api.main import app
from app.core.env import User_Settings, Postgres_Settings
import asyncpg
from datetime import datetime, timedelta, timezone

USER_SETTINGS=User_Settings()
POSTGRES_SEETTINGS=Postgres_Settings()
AMBIGUOUS_ERROR= "The email and/or passwordare invalid"

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

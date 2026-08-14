import pytest
from fastapi.testclient import TestClient
from app.api.main import app
from app.core.env import User_Settings, Postgres_Settings, Auth_Settings
import asyncpg
from datetime import datetime, timedelta, timezone
import uuid as uuidlib
from app.auth.auth import create_token, COOKIE_NAME, INVALID_TOKEN, NOT_AUTH, EXPIRED_TOKEN
import asyncio
from jose import jwt

USER_SETTINGS=User_Settings()
POSTGRES_SETTINGS=Postgres_Settings()
AMBIGUOUS_ERROR= "The email and/or password are invalid"
AUTH_SETTINGS = Auth_Settings()

ADMIN_USER = None
E2E_USER = None

@pytest.fixture(scope="session", autouse=True)
def load_e2e_user():
    global E2E_USER

    async def fetch_user():
        connection = await get_connection()

        try:
            return await connection.fetchrow(
                """
                SELECT userid, username
                FROM "Users_DB"."Users"
                WHERE useremail = $1
                """,
                USER_SETTINGS.E2E_USER_EMAIL
            )
        finally:
            await connection.close()

    E2E_USER = asyncio.run(fetch_user())
    assert E2E_USER is not None

@pytest.fixture(scope="session", autouse=True)
def load_admin_user():
    global ADMIN_USER

    async def fetch_admin():
        connection = await get_connection()

        try:
            return await connection.fetchrow(
                """
                SELECT userid, username
                FROM "Users_DB"."Users"
                WHERE useremail = $1
                """,
                USER_SETTINGS.ADMIN_EMAIL
            )
        finally:
            await connection.close()

    ADMIN_USER = asyncio.run(fetch_admin())
    assert ADMIN_USER is not None

async def get_connection() -> asyncpg.Connection:
    return await asyncpg.connect(
        user=POSTGRES_SETTINGS.DB_USER,
        password=POSTGRES_SETTINGS.DB_PASSWORD,
        database=POSTGRES_SETTINGS.DB_NAME,
        host=POSTGRES_SETTINGS.DB_HOST,
        port=POSTGRES_SETTINGS.DB_PORT,
        ssl="require" if POSTGRES_SETTINGS.DB_SSL else None,
    )

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.mark.asyncio
async def test_integration_create_case_success(client):
    case_name = "Integration Create Case Test"
    case_id = None

    try:
        admin_user = {
            "id": str(ADMIN_USER["userid"]),
            "username": ADMIN_USER["username"],
            "role": "ADMIN"
        }

        admin_token = create_token(admin_user)

        client.cookies.clear()
        client.cookies.set(
            COOKIE_NAME,
            admin_token
        )

        response = client.post(
            "/api/createCase",
            json={
                "title": case_name,
                "description": "Case created during integration testing."
            }
        )

        assert response.status_code == 200
        response_data = response.json()

        assert response_data["status"] == "success"
        assert "CaseId" in response_data

        case_id = response_data["CaseId"]

        connection = await get_connection()

        try:
            created_case = await connection.fetchrow(
                """
                SELECT
                    caseid,
                    casecreator,
                    casename,
                    casedescription,
                    caseclosed
                FROM "Cases_DB"."Cases"
                WHERE caseid = $1
                """,
                uuidlib.UUID(case_id)
            )
        finally:
            connection.close()

        assert created_case is not None
        assert str(created_case["caseid"]) == case_id
        assert created_case["casecreator"] == ADMIN_USER["username"]
        assert created_case["casename"] == case_name
        assert created_case["casedescription"] == "Case created during integration testing."
        assert created_case["caseclosed"] is False
    finally:
        if case_id is not None:
            connection = await get_connection()

            try:
                await connection.execute(
                    """
                    DELETE from "Cases_DB"."Cases"
                    WHERE caseid = $1
                    """,
                    uuidlib.UUID(case_id)
                )
            finally:
                await connection.close()

@pytest.mark.asyncio
async def test_integration_create_case_missing_jwt(client):
    client.cookies.clear()

    response = client.post(
        "/api/createCase",
        json={
            "title": "Test case",
            "description": "Test description"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": NOT_AUTH
        }
    }

@pytest.mark.asyncio
async def test_integration_create_case_invalid_jwt(client):
    client.cookies.clear()
    client.cookies.set(
        COOKIE_NAME,
        "invalid-token"
    )

    response = client.post(
        "/api/createCase",
        json={
            "title": "Test Case",
            "description": "Test description"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": INVALID_TOKEN
        }
    }

@pytest.mark.asyncio
async def test_integration_create_case_expired_jwt(client):
    expired_token = jwt.encode(
        {
            "sub": str(ADMIN_USER["userid"]),
            "username": ADMIN_USER["username"],
            "role": "ADMIN",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=10)
        },
        AUTH_SETTINGS.JWT_SECRET,
        algorithm=AUTH_SETTINGS.HASH
    )

    client.cookies.clear()
    client.cookies.set(
        COOKIE_NAME,
        expired_token
    )

    response = client.post(
        "/api/createCase",
        json={
            "title": "Test Case",
            "description": "Test description"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": EXPIRED_TOKEN
        }
    }

@pytest.mark.asyncio
async def test_integration_create_case_user_unauthorized(client):
    user = {
        "id": str(uuidlib.uuid4()),
        "username": "integration_user",
        "role": "USER"
    }

    token = create_token(user)

    client.cookies.clear()
    client.cookies.set(
        COOKIE_NAME,
        token
    )

    response = client.post(
        "/api/createCase",
        json={
            "title": "Unauthorized Case",
            "description": "This case should not be created."
        }
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "User unauthorized"
        }
    }

@pytest.mark.asyncio
async def test_integration_create_case_empty_name(client):
    admin_user = {
        "id": str(ADMIN_USER["userid"]),
        "username": ADMIN_USER["username"],
        "role": "ADMIN"
    }

    admin_token = create_token(admin_user)
    client.cookies.clear()
    client.cookies.set(
        COOKIE_NAME,
        admin_token
    )

    response = client.post(
        "/api/createCase",
        json={
            "title": "",
            "description": "Test description"
        }
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "CaseName is required"
        }
    }

@pytest.mark.asyncio
async def test_integration_create_case_name_too_long(client):
    admin_user = {
        "id": str(ADMIN_USER["userid"]),
        "username": ADMIN_USER["username"],
        "role": "ADMIN"
    }

    admin_token = create_token(admin_user)

    client.cookies.clear()
    client.cookies.set(
        COOKIE_NAME,
        admin_token
    )

    response = client.post(
        "/api/createCase",
        json={
            "title": "A" * 256,
            "description": "Test description"
        }
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "CaseName must be 255 characters or less"
        }
    }
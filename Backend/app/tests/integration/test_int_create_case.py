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
from test_int_auth import delete_user_by_email
from app.tests.integration.conftest import get_connection
from app.tests.integration.test_int_auth import  load_admin_user # for sonar
import app.tests.integration.test_int_auth as auth_tests # for sonar


USER_SETTINGS=User_Settings()
POSTGRES_SETTINGS=Postgres_Settings()
AMBIGUOUS_ERROR= "The email and/or password are invalid"
AUTH_SETTINGS = Auth_Settings()


@pytest.mark.asyncio
async def test_integration_create_case_success(client):
    case_name = "Integration Create Case Test"
    case_id = None
    user_id=str(auth_tests.ADMIN_USER["userid"])
    try:
        admin_user = {
            "id": user_id,
            "username": auth_tests.ADMIN_USER["username"],
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

        assert response.status_code == 201
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
            await connection.close()

        assert created_case is not None
        assert str(created_case["caseid"]) == case_id
        assert created_case["casecreator"] == auth_tests.ADMIN_USER["username"]
        assert created_case["casename"] == case_name
        assert created_case["casedescription"] == "Case created during integration testing."
        assert created_case["caseclosed"] is False
    finally:
        if case_id is not None:
            connection = await get_connection()

            try:
                await connection.execute("SELECT set_config('app.current_user_id', $1, false)", user_id)
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
            "sub": str(auth_tests.ADMIN_USER["userid"]),
            "username": auth_tests.ADMIN_USER["username"],
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
    email = "create_case_unauthorized@example.com"

    await delete_user_by_email(email)

    try:
        client.cookies.clear()

        register_response = client.post(
            "/api/register",
            json={
                "email": email,
                "username": "create_case_unauthorized",
                "password": USER_SETTINGS.ADMIN_PASSWORD
            }
        )
        assert register_response.status_code == 201
        assert COOKIE_NAME in client.cookies

        response = client.post(
            "/api/createCase",
            json={
                "title": "Unauthorized Case",
                "description": "This case should not be created."
            }
        )

        assert response.status_code == 401
        assert response.json() == {
            "detail": {
                "status": "error",
                "message": NOT_AUTH
            }
        }

    finally:
        await delete_user_by_email(email)

@pytest.mark.asyncio
async def test_integration_create_case_empty_name(client):
    admin_user = {
        "id": str(auth_tests.ADMIN_USER["userid"]),
        "username": auth_tests.ADMIN_USER["username"],
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
        "id": str(auth_tests.ADMIN_USER["userid"]),
        "username": auth_tests.ADMIN_USER["username"],
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
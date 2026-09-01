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
from app.tests.integration.test_int_auth import load_admin_user # for sonar
import app.tests.integration.test_int_auth as auth_tests # for sonar
from app.api.routers.cases_router import CASE_ID_REQUIRED, INVALID_CASE_ID, CASE_NOT_FOUND_OR_UNAUTHORIZED

USER_SETTINGS = User_Settings()

@pytest.mark.asyncio
async def test_integration_close_case_success(client, load_admin_user):
    case_id = None
    executor_id = str(auth_tests.ADMIN_USER["userid"])
    admin_user = {
        "id": executor_id,
        "username": auth_tests.ADMIN_USER["username"],
        "role": "ADMIN"
    }

    admin_token = create_token(admin_user)

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, admin_token)

    try:
        create_response = client.post(
            "/api/createCase",
            json={
                "title": "Close Case Integration Test",
                "description": "Case created for closeCase integration testing."
            }
        )

        assert create_response.status_code == 201

        case_id = create_response.json()["CaseId"]

        response = client.post(
            "/api/closeCase",
            json={
                "CaseID": case_id
            }
        )

        assert response.status_code == 200
        assert response.json() == {
            "status": "success",
            "message": "Case closed successfully."
        }

        connection = await get_connection()

        try:
            row = await connection.fetchrow(
                """
                SELECT caseclosed
                FROM "Cases_DB"."Cases"
                WHERE caseid = $1
                """,
                uuidlib.UUID(case_id)
            )
        finally:
            await connection.close()

        assert row is not None
        assert row["caseclosed"] is True

    finally:
        if case_id is not None:
            connection = await get_connection()

            try:
                await connection.execute("SELECT set_config('app.current_user_id', $1, false)", executor_id)
                await connection.execute(
                    """
                    DELETE FROM "Cases_DB"."Cases"
                    WHERE caseid = $1
                    """,
                    uuidlib.UUID(case_id)
                )

            finally:
                await connection.close()

@pytest.mark.asyncio
async def test_integration_close_case_success_investigator(client):
    case_id = None

    connection = await get_connection()

    try:
        investigator = await connection.fetchrow(
            """
            SELECT userid, username
            FROM "Users_DB"."Users"
            WHERE useremail = $1
            """,
            USER_SETTINGS.E2E_INVESTIGATOR_EMAIL
        )
    finally:
        await connection.close()

    assert investigator is not None

    executor_id = str(investigator["userid"])
    investigator_user = {
        "id": executor_id ,
        "username": investigator["username"],
        "role": "INVESTIGATOR"
    }

    investigator_token = create_token(investigator_user)

    client.cookies.clear()
    client.cookies.set(
        COOKIE_NAME,
        investigator_token
    )

    try:
        create_response = client.post(
            "/api/createCase",
            json={
                "title": "Investigator Close Case Integration Test",
                "description": "Case created by an investigator for closeCase integration testing."
            }
        )

        assert create_response.status_code == 201

        case_id = create_response.json()["CaseId"]
        response = client.post(
            "/api/closeCase",
            json={
                "CaseID": case_id
            }
        )

        assert response.status_code == 200

        assert response.json() == {
            "status": "success",
            "message": "Case closed successfully."
        }

        connection = await get_connection()

        try:
            
            row = await connection.fetchrow(
                """
                SELECT caseclosed
                FROM "Cases_DB"."Cases"
                WHERE caseid = $1
                """,
                uuidlib.UUID(case_id)
            )
        finally:
            await connection.close()

        assert row is not None
        assert row["caseclosed"] is True

    finally:
        if case_id is not None:
            connection = await get_connection()

            try:
                await connection.execute("SELECT set_config('app.current_user_id', $1, false)", executor_id)
                await connection.execute(
                    """
                    DELETE FROM "Cases_DB"."Cases"
                    WHERE caseid = $1
                    """,
                    uuidlib.UUID(case_id)
                )

            finally:
                await connection.close()

@pytest.mark.asyncio
async def test_integration_close_case_missing_case_id(client, load_admin_user):
    admin_user = {
        "id": str(auth_tests.ADMIN_USER["userid"]),
        "username": auth_tests.ADMIN_USER["username"],
        "role": "ADMIN"
    }

    client.cookies.clear()
    client.cookies.set(
        COOKIE_NAME,
        create_token(admin_user)
    )

    response = client.post(
        "/api/closeCase",
        json={
            "CaseID": ""
        }
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": CASE_ID_REQUIRED
        }
    }

@pytest.mark.asyncio
async def test_integration_close_case_invalid_case_id(client, load_admin_user):
    admin_user = {
        "id": str(auth_tests.ADMIN_USER["userid"]),
        "username": auth_tests.ADMIN_USER["username"],
        "role": "ADMIN"
    }

    client.cookies.clear()
    client.cookies.set(
        COOKIE_NAME,
        create_token(admin_user)
    )

    response = client.post(
        "/api/closeCase",
        json={
            "CaseID": "not-a-valid-uuid"
        }
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": INVALID_CASE_ID
        }
    }

@pytest.mark.asyncio
async def test_integration_close_case_missing_jwt(client):
    client.cookies.clear()

    response = client.post(
        "/api/closeCase",
        json={
            "CaseID": str(uuidlib.uuid4())
        }
    )

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_integration_close_case_invalid_jwt(client):
    client.cookies.clear()
    client.cookies.set(
        COOKIE_NAME,
        "invalid-token"
    )

    response = client.post(
        "/api/closeCase",
        json={
            "CaseID": str(uuidlib.uuid4())
        }
    )

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_integration_close_case_user_unauthorized(client):
    email = "close_case_user@example.com"
    await delete_user_by_email(email)

    try: 
        client.cookies.clear()
        register_response = client.post(
            "/api/register",
            json={
                "email": email,
                "username": "close_case_user",
                "password": USER_SETTINGS.ADMIN_PASSWORD
            }
        )

        assert register_response.status_code == 201
        response = client.post(
            "/api/closeCase",
            json={
                "CaseID": str(uuidlib.uuid4())
            }
        )

        assert response.status_code == 401

    finally:
        await delete_user_by_email(email)

@pytest.mark.asyncio
async def test_integration_close_case_not_found(client, load_admin_user):
    admin_user = {
        "id": str(auth_tests.ADMIN_USER["userid"]),
        "username": auth_tests.ADMIN_USER["username"],
        "role": "ADMIN"
    }

    client.cookies.clear()
    client.cookies.set(
        COOKIE_NAME,
        create_token(admin_user)
    )

    response = client.post(
        "/api/closeCase",
        json={
            "CaseID": str(uuidlib.uuid4())
        }
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": CASE_NOT_FOUND_OR_UNAUTHORIZED
        }
    }
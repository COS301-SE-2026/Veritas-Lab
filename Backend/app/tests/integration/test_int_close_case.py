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
from app.tests.integration.test_int_auth import client, get_connection, load_admin_user # for sonar
import app.tests.integration.test_int_auth as auth_tests # for sonar
from app.api.routers.cases_router import CASE_ID_REQUIRED

@pytest.mark.asyncio
async def test_integration_close_case_success(client, load_admin_user):
    case_id = None
    admin_user = {
        "id": str(auth_tests.ADMIN_USER["userid"]),
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
                await connection.execute(
                    """
                    DELETE FROM "CasesDB"."Cases"
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
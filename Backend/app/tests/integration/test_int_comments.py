import pytest
from fastapi.testclient import TestClient
from app.api.main import app
from app.core.env import User_Settings, Postgres_Settings, Auth_Settings
import asyncpg
from datetime import datetime, timedelta, timezone
import uuid as uuidlib
from app.auth.auth import create_token, COOKIE_NAME, INVALID_TOKEN
import asyncio
from jose import jwt

USER_SETTINGS=User_Settings()
POSTGRES_SEETTINGS=Postgres_Settings()
AUTH_SETTINGS = Auth_Settings()

INVEST_USER = None

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

async def get_connection() -> asyncpg.Connection:
    return await asyncpg.connect(
        user=POSTGRES_SEETTINGS.DB_USER,
        password=POSTGRES_SEETTINGS.DB_PASSWORD,
        database=POSTGRES_SEETTINGS.DB_NAME,
        host=POSTGRES_SEETTINGS.DB_HOST,
        port=POSTGRES_SEETTINGS.DB_PORT,
        ssl="require" if POSTGRES_SEETTINGS.DB_SSL else None,
    )

@pytest.fixture(scope="session", autouse=True)
def load_investigator_user():
    global INVEST_USER

    async def fetch_investigator():
        connection = await get_connection()
    
        try:
            return await connection.fetchrow(
                """
                SELECT userid, username
                FROM "Users_DB"."Users"
                WHERE useremail = $1
                """,
                USER_SETTINGS.E2E_INVESTIGATOR_EMAIL
            )
        finally:
            await connection.close()
    
    INVEST_USER = asyncio.run(fetch_investigator())
    assert INVEST_USER is not None

@pytest.mark.asyncio
async def test_integration_delete_comment_success(client):
    investigator = {
        "id": str(INVEST_USER["userid"]),
        "username": INVEST_USER["username"],
        "role": "INVESTIGATOR"
    }

    investigator_token = create_token(investigator)

    client.cookies.clear()
    client.cookies.set(
        COOKIE_NAME,
        investigator_token
    )

    case_response = client.post(
        "/api/createCase",
        json={
            "title": "Delete Comment Integration Test",
            "description": "Temporary case for delete comment integration test"
        }
    )

    assert case_response.status_code == 201

    case_id = case_response.json()["CaseId"]

    comment_response = client.post(
        "/api/cases/comments",
        json={
            "case_id": case_id,
            "comment": "Comment to be deleted during integration testing"
        }
    )

    assert comment_response.status_code == 201

    comment_id = comment_response.json()["comment"]["commentId"]

    response = client.delete(f"/api/deleteComment/comment/{comment_id}")

    assert response.status_code == 200

    assert response.json() == {
        "status": "success",
        "message": "Comment deleted successfully."
    }

    connection = await get_connection()

    try:
        deleted_comment = await connection.fetchrow(
            """
            SELECT commentid
            FROM "Cases_DB"."Comments"
            WHERE commentid = $1
            """,
            comment_id
        )

        assert deleted_comment is None

    finally:
        await connection.close()

@pytest.mark.asyncio
async def test_integration_delete_comment_not_found(client):
    investigator = {
        "id": str(INVEST_USER["userid"]),
        "username": INVEST_USER["username"],
        "role": "INVESTIGATOR"
    }

    investigator_token = create_token(investigator)

    client.cookies.clear()
    client.cookies.set(
        COOKIE_NAME,
        investigator_token
    )

    response = client.delete("/api/deleteComment/comment/999999999")

    assert response.status_code == 404

    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Comment not found or user unauthorized"
        }
    }

@pytest.mark.asyncio
async def test_integration_delete_comment_no_auth(client):
    client.cookies.clear()

    response = client.delete(
        "/api/deleteComment/comment/999999999"
    )

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_integration_delete_comment_invalid_token(client):
    client.cookies.clear()
    client.cookies.set(
        COOKIE_NAME,
        "this-is-not-a-valid-jwt"
    )

    response = client.delete("/api/deleteComment/comment/999999999")

    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": INVALID_TOKEN
        }
    }







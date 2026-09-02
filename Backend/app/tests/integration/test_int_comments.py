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
from app.tests.integration.conftest import get_connection

USER_SETTINGS=User_Settings()
POSTGRES_SEETTINGS=Postgres_Settings()
AUTH_SETTINGS = Auth_Settings()

INVEST_USER = None
ADMIN_USER = None


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

@pytest.mark.asyncio
async def test_integration_delete_comment_not_owner(client):
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
            "title": "Delete Comment Ownership Test",
            "description": "Temporary case for ownership integration test"
        }
    )

    assert case_response.status_code == 201

    case_id = case_response.json()["CaseId"]

    comment_response = client.post(
        "/api/cases/comments",
        json={
            "case_id": case_id,
            "comment": "Investigator owns this comment"
        }
    )

    assert comment_response.status_code == 201

    comment_id = comment_response.json()["comment"]["commentId"]

    admin = {
        "id": str(ADMIN_USER["userid"]),
        "username": ADMIN_USER["username"],
        "role": "ADMIN"
    }

    admin_token = create_token(admin)

    client.cookies.clear()
    client.cookies.set(
        COOKIE_NAME,
        admin_token
    )

    response = client.delete(f"/api/deleteComment/comment/{comment_id}")

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Comment not found or user unauthorized"
        }
    }

    connection = await get_connection()

    try:
        comment = await connection.fetchrow(
            """
            SELECT commentid
            FROM "Cases_DB"."Comments"
            WHERE commentid = $1
            """,
            comment_id
        )

        assert comment is not None

    finally:
        await connection.close()

@pytest.mark.asyncio
async def test_integration_edit_comment_success(client):
    investigator = {
        "id": str(INVEST_USER["userid"]),
        "username": INVEST_USER["username"],
        "role": "INVESTIGATOR"
    }

    client.cookies.clear()
    client.cookies.set(
        COOKIE_NAME,
        create_token(investigator)
    )

    case_response = client.post(
        "/api/createCase",
        json={
            "title": "Edit Comment Integration Test",
            "description": "Temp case"
        }
    )
    assert case_response.status_code == 201
    case_id = case_response.json()["CaseId"]

    comment_response = client.post(
        "/api/cases/comments",
        json={
            "case_id": case_id,
            "comment": "Original comment"
        }
    )
    assert comment_response.status_code == 201
    comment_id = comment_response.json()["comment"]["commentId"]

    edit_response = client.post(
        f"/api/editComment/case/{case_id}/comment/{comment_id}",
        json={"comment": "Edited comment"}
    )
    assert edit_response.status_code == 200
    assert edit_response.json() == {
        "status": "success",
        "message": "Comment edit successfully.",
    }

    connection = await get_connection()
    try:
        row = await connection.fetchrow(
            """
            SELECT comment
            FROM "Cases_DB"."Comments"
            WHERE commentid = $1
            """,
            comment_id
        )
        assert row is not None
        assert row["comment"] == "Edited comment"
    finally:
        await connection.close()

@pytest.mark.asyncio
async def test_integration_edit_comment_not_owner(client):
    inverstigator = {
        "id": str(INVEST_USER["userid"]),
        "username": INVEST_USER["username"],
        "role": "INVESTIGATOR"
    }
    client.cookies.clear()
    client.cookies.set(
        COOKIE_NAME,
        create_token(inverstigator)
    )

    case_response = client.post(
        "/api/createCase",
        json={
            "title": "Edit Comment Not Owner Test",
            "description": "Temp case"
        }
    )
    case_id = case_response.json()["CaseId"]

    comment_response = client.post(
        "/api/cases/comments",
        json={
            "case_id": case_id,
            "comment": "Comment by investigator as the owner"
        }
    )
    comment_id = comment_response.json()["comment"]["commentId"]

    admin = {
        "id": str(ADMIN_USER["userid"]),
        "username": ADMIN_USER["username"],
        "role": "ADMIN"
    }
    client.cookies.clear()
    client.cookies.set(
        COOKIE_NAME,
        create_token(admin)
    )

    #this is to attaempt to edit an investigator's comment as an admin, which should fail
    edit_response = client.post(
        f"/api/editComment/case/{case_id}/comment/{comment_id}",
        json={"comment": "Attempt to edit a comment not made by admin"}
    )

    assert edit_response.status_code == 404
    assert edit_response.json() == {
        "detail": {
            "status": "error",
            "message": "Case not found or user unauthorized."
        }
    }
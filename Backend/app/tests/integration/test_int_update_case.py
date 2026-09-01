import pytest
import pytest_asyncio
import uuid
import asyncpg
from fastapi.testclient import TestClient
from app.tests.integration.conftest import get_connection
from app.api.main import app
from app.core.env import Postgres_Settings
from app.auth.auth import create_token, COOKIE_NAME

POSTGRES_SETTINGS = Postgres_Settings()

# The JWT username must match Cases.CaseCreator exactly, the endpoint updates on it.
OWNER_USERNAME = "TestUpdateOwner"
OTHER_USERNAME = "TestUpdateOther"

OWNER_USER_ID = "00000000-0000-0000-0000-000000000001"
OTHER_USER_ID = "00000000-0000-0000-0000-000000000002"

ORIGINAL_NAME = "Integration Test - update case"
ORIGINAL_DESCRIPTION = "The original description"

def owner_cookie():
    return create_token({
        "id": OWNER_USER_ID,
        "username": OWNER_USERNAME,
        "role": "INVESTIGATOR"
    })


def other_investigator_cookie():
    return create_token({
        "id": OTHER_USER_ID,
        "username": OTHER_USERNAME,
        "role": "INVESTIGATOR"
    })


def user_cookie():
    return create_token({
        "id": str(uuid.uuid4()),
        "username": OWNER_USERNAME,
        "role": "USER"
    })


async def fetch_case(conn, case_id):
    return await conn.fetchrow(
        """
        SELECT casename, casedescription
        FROM "Cases_DB"."Cases"
        WHERE caseid = $1
        """,
        uuid.UUID(case_id)
    )


@pytest_asyncio.fixture
async def fake_update_case_context(ensure_user_exists):
    conn = await get_connection()
    created_ids = {"connection": conn}

    try:
        await ensure_user_exists(conn, OWNER_USER_ID, OWNER_USERNAME, "INVESTIGATOR")
        await ensure_user_exists(conn, OTHER_USER_ID, OTHER_USERNAME, "INVESTIGATOR")

        for label, creator in (("owned", OWNER_USERNAME), ("foreign", OTHER_USERNAME)):
            case_id = str(uuid.uuid4())
            await conn.execute("SELECT set_config('app.current_user_id', $1, false)", OWNER_USER_ID)
            await conn.execute(
                """
                INSERT INTO "Cases_DB"."Cases"
                (CaseId, CaseName, CaseCreator, CaseDescription, CaseClosed)
                VALUES ($1, $2, $3, $4, $5)
                """,
                uuid.UUID(case_id),
                f"{ORIGINAL_NAME} - {label}",
                creator,
                ORIGINAL_DESCRIPTION,
                False,
            )
            created_ids[f"{label}_case_id"] = case_id
        yield created_ids
    finally:
        await conn.execute("SELECT set_config('app.current_user_id', $1, false)", OWNER_USER_ID)
        for case_id in (created_ids.get("owned_case_id"), created_ids.get("foreign_case_id")):
            if case_id:
                await conn.execute('DELETE FROM "Cases_DB"."Cases" WHERE caseid = $1', uuid.UUID(case_id))
        await conn.execute("SELECT set_config('app.current_user_id', '', false)")
        await conn.close()


@pytest.mark.asyncio
async def test_integration_update_case_name_only(client, fake_update_case_context):
    client.cookies.set(COOKIE_NAME, owner_cookie())
    case_id = fake_update_case_context["owned_case_id"]

    response = client.post(
        "/api/updateCase",
        json={
            "CaseID": case_id,
            "CaseName": "Renamed by integration test"
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Case updated successfully."
    }

    row = await fetch_case(fake_update_case_context["connection"], case_id)

    assert row["casename"] == "Renamed by integration test"
    assert row["casedescription"] == ORIGINAL_DESCRIPTION


@pytest.mark.asyncio
async def test_integration_update_case_description_only(client, fake_update_case_context):
    client.cookies.set(COOKIE_NAME, owner_cookie())
    case_id = fake_update_case_context["owned_case_id"]

    response = client.post(
        "/api/updateCase",
        json={
            "CaseID": case_id,
            "CaseDescription": "Rewritten by integration test"
        }
    )

    assert response.status_code == 200

    row = await fetch_case(fake_update_case_context["connection"], case_id)

    assert row["casedescription"] == "Rewritten by integration test"
    assert row["casename"] == f"{ORIGINAL_NAME} - owned"


@pytest.mark.asyncio
async def test_integration_update_case_both_fields(client, fake_update_case_context):
    client.cookies.set(COOKIE_NAME, owner_cookie())
    case_id = fake_update_case_context["owned_case_id"]

    response = client.post(
        "/api/updateCase",
        json={
            "CaseID": case_id,
            "CaseName": "  Both fields updated  ",
            "CaseDescription": "Both fields description"
        }
    )

    assert response.status_code == 200

    row = await fetch_case(fake_update_case_context["connection"], case_id)

    assert row["casename"] == "Both fields updated"
    assert row["casedescription"] == "Both fields description"


@pytest.mark.asyncio
async def test_integration_update_case_user_role_forbidden(client, fake_update_case_context):
    client.cookies.set(COOKIE_NAME, user_cookie())
    case_id = fake_update_case_context["owned_case_id"]

    response = client.post(
        "/api/updateCase",
        json={
            "CaseID": case_id,
            "CaseName": "USER should not be able to do this"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"]["message"] == "User unauthorized"

    row = await fetch_case(fake_update_case_context["connection"], case_id)

    assert row["casename"] == f"{ORIGINAL_NAME} - owned"


@pytest.mark.asyncio
async def test_integration_update_case_not_the_creator(client, fake_update_case_context):
    client.cookies.set(COOKIE_NAME, owner_cookie())
    case_id = fake_update_case_context["foreign_case_id"]

    response = client.post(
        "/api/updateCase",
        json={
            "CaseID": case_id,
            "CaseName": "Stolen case"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"]["message"] == "Case not found or user unauthorized."

    row = await fetch_case(fake_update_case_context["connection"], case_id)

    assert row["casename"] == f"{ORIGINAL_NAME} - foreign"


@pytest.mark.asyncio
async def test_integration_update_case_unknown_case(client):
    client.cookies.set(COOKIE_NAME, owner_cookie())

    response = client.post(
        "/api/updateCase",
        json={
            "CaseID": str(uuid.uuid4()),
            "CaseName": "Nothing to update"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"]["status"] == "error"


@pytest.mark.asyncio
async def test_integration_update_case_malformed_case_id(client):
    client.cookies.set(COOKIE_NAME, owner_cookie())

    response = client.post(
        "/api/updateCase",
        json={
            "CaseID": "not-a-valid-uuid",
            "CaseName": "Whatever"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "'not-a-valid-uuid' is not a valid UUID format"


@pytest.mark.asyncio
async def test_integration_update_case_missing_case_id(client):
    client.cookies.set(COOKIE_NAME, owner_cookie())

    response = client.post(
        "/api/updateCase",
        json={"CaseName": "Whatever"}
    )

    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "CaseID required"


@pytest.mark.asyncio
async def test_integration_update_case_no_fields(client, fake_update_case_context):
    client.cookies.set(COOKIE_NAME, owner_cookie())

    response = client.post(
        "/api/updateCase",
        json={"CaseID": fake_update_case_context["owned_case_id"]}
    )

    assert response.status_code == 400
    assert response.json()["detail"]["message"] == (
        "At least one of CaseName or CaseDescription must be provided"
    )


@pytest.mark.asyncio
async def test_integration_update_case_blank_name(client, fake_update_case_context):
    client.cookies.set(COOKIE_NAME, owner_cookie())
    case_id = fake_update_case_context["owned_case_id"]

    response = client.post(
        "/api/updateCase",
        json={
            "CaseID": case_id,
            "CaseName": "   "
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "CaseName is required"

    row = await fetch_case(fake_update_case_context["connection"], case_id)

    assert row["casename"] == f"{ORIGINAL_NAME} - owned"


@pytest.mark.asyncio
async def test_integration_update_case_name_too_long(client, fake_update_case_context):
    client.cookies.set(COOKIE_NAME, owner_cookie())

    response = client.post(
        "/api/updateCase",
        json={
            "CaseID": fake_update_case_context["owned_case_id"],
            "CaseName": "A" * 256
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "CaseName must be 255 characters or less"


@pytest.mark.asyncio
async def test_integration_update_case_unauthenticated(client, fake_update_case_context):
    client.cookies.clear()

    response = client.post(
        "/api/updateCase",
        json={
            "CaseID": fake_update_case_context["owned_case_id"],
            "CaseName": "No cookie"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"]["status"] == "error"

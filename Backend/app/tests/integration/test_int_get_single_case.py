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


def investigator_cookie():
    return create_token({
        "id": str(uuid.uuid4()),
        "username": "Testinvestigator",
        "role": "INVESTIGATOR"
    })

def user_cookie():
    return create_token({
        "id": str(uuid.uuid4()),
        "username": "Testuser",
        "role": "USER"
    })

@pytest_asyncio.fixture
async def fake_get_single_case_context(ensure_user_exists):
    conn = await get_connection()
    created_ids = {}

    try:
        admin_id = str(uuid.uuid4())
        await ensure_user_exists(conn, admin_id, "admin_user", role="ADMIN")
        created_ids["admin_id"] = admin_id

        await conn.execute("SELECT set_config('app.current_user_id', $1, false)", admin_id)

        media_type_id = str(uuid.uuid4())
        unique_suffix = uuid.uuid4().hex[:6]
        await conn.execute(
            """
            INSERT INTO "Cases_DB"."MediaType"
            (MediaTypeId, MediaName, MediaBucket, MediaExtension)
            VALUES ($1, $2, $3, $4)
            """,
            uuid.UUID(media_type_id),
            f"SINGLE_CASE_{unique_suffix}",
            "test-bucket",
            f".{unique_suffix}"
        )
        created_ids["media_type_id"] = media_type_id

        for label, closed in (("open", False), ("closed", True)):
            media_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO "Cases_DB"."Media"
                (MediaId, MediaType, MediaHash)
                VALUES ($1, $2, $3)
                """,
                uuid.UUID(media_id),
                uuid.UUID(media_type_id),
                uuid.uuid4().hex
            )
            created_ids[f"{label}_media_id"] = media_id

            case_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO "Cases_DB"."Cases"
                (CaseId, CaseName, CaseCreator, CaseDescription, CaseClosed)
                VALUES ($1, $2, $3, $4, $5)
                """,
                uuid.UUID(case_id),
                f"Integration Test - {label} case",
                "TestInvestigator",
                f"This case is currently {label}",
                closed
            )
            created_ids[f"{label}_case_id"] = case_id

            await conn.execute(
                """
                INSERT INTO "Cases_DB"."Reports"
                (CaseId, MediaId, ImageTitle)
                VALUES ($1, $2, $3)
                """,
                uuid.UUID(case_id),
                uuid.UUID(media_id),
                f"{label}-evidence"
            )

        yield created_ids

    finally:
        for label in ("open", "closed"):
            if f"{label}_case_id" in created_ids:
                await conn.execute(
                    'DELETE FROM "Cases_DB"."Cases" WHERE CaseId = $1',
                    uuid.UUID(created_ids[f"{label}_case_id"])
                )
            if f"{label}_media_id" in created_ids:
                await conn.execute(
                    'DELETE FROM "Cases_DB"."Media" WHERE MediaId = $1',
                    uuid.UUID(created_ids[f"{label}_media_id"])
                )

        if "media_type_id" in created_ids:
            await conn.execute(
                'DELETE FROM "Cases_DB"."MediaType" WHERE MediaTypeId = $1',
                uuid.UUID(created_ids["media_type_id"])
            )

        await conn.close()

@pytest.mark.asyncio
async def test_integration_get_single_case_investigator_open_case(client, fake_get_single_case_context):
    client.cookies.set(COOKIE_NAME, investigator_cookie())

    response = client.post(
        "/api/getSingleCase",
        json={"CaseID": fake_get_single_case_context["open_case_id"]}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["case"]["caseId"] == fake_get_single_case_context["open_case_id"]
    assert data["case"]["caseClosed"] is False

    assert len(data["evidence"]) == 1
    assert data["evidence"][0]["mediaUrl"] != ""

@pytest.mark.asyncio
async def test_integration_get_single_case_user_closed_case(client, fake_get_single_case_context):
    client.cookies.set(COOKIE_NAME, user_cookie())

    response = client.post(
        "/api/getSingleCase",
        json={"CaseID": fake_get_single_case_context["closed_case_id"]}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["case"]["caseId"] == fake_get_single_case_context["closed_case_id"]
    assert data["case"]["caseClosed"] is True

    assert len(data["evidence"]) == 1
    assert data["evidence"][0]["mediaUrl"] == ""

@pytest.mark.asyncio
async def test_integration_get_single_case_user_cannot_see_open_case(client, fake_get_single_case_context):
    client.cookies.set(COOKIE_NAME, user_cookie())

    response = client.post(
        "/api/getSingleCase",
        json={"CaseID": fake_get_single_case_context["open_case_id"]}
    )

    assert response.status_code == 404
    assert response.json()["detail"]["message"] == "Case not found"

@pytest.mark.asyncio
async def test_integration_get_single_case_unknown_case(client):
    client.cookies.set(COOKIE_NAME, investigator_cookie())

    response = client.post(
        "/api/getSingleCase",
        json={"CaseID": str(uuid.uuid4())}
    )

    assert response.status_code == 404
    assert response.json()["detail"]["status"] == "error"

@pytest.mark.asyncio
async def test_integration_get_single_case_malformed_case_id(client):
    client.cookies.set(COOKIE_NAME, investigator_cookie())

    response = client.post(
        "/api/getSingleCase",
        json={"CaseID": "not-a-valid-uuid"}
    )

    assert response.status_code == 400
    assert response.json()["detail"]["status"] == "error"

@pytest.mark.asyncio
async def test_integration_get_single_case_missing_case_id(client):
    client.cookies.set(COOKIE_NAME, investigator_cookie())

    response = client.post(
        "/api/getSingleCase",
        json={}
    )

    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "CaseID required"

@pytest.mark.asyncio
async def test_integration_get_single_case_unauthorized(client):
    response = client.post(
        "/api/getSingleCase",
        json={"CaseID": str(uuid.uuid4())}
    )

    assert response.status_code == 401
    assert response.json()["detail"]["status"] == "error"
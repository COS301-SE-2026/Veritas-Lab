import pytest
from fastapi.testclient import TestClient
from app.api.main import app
import pytest_asyncio
import uuid
from app.auth.auth import create_token, COOKIE_NAME
from app.tests.integration.test_int_annotations import get_connection, client

@pytest_asyncio.fixture
async def fake_get_cases_context():
    conn = await get_connection()
    created_ids = {}

    try:
        open_case_id = str(uuid.uuid4())
        await conn.execute(
            """INSERT INTO "Cases_DB"."Cases" (CaseId, CaseName, CaseCreator, CaseDescription, CaseClosed)
                VALUES ($1, $2, $3, $4, $5)
                """,
            uuid.UUID(open_case_id),
            "Integration Test - Open Case",
            "TestInvestigator",
            "This case is currently open",
            False
        )
        created_ids["open_case_id"] = open_case_id

        closed_case_id = str(uuid.uuid4())
        await conn.execute(
            """INSERT INTO "Cases_DB"."Cases" (CaseId, CaseName, CaseCreator, CaseDescription, CaseClosed)
                VALUES ($1, $2, $3, $4, $5)
                """,
            uuid.UUID(closed_case_id),
            "Integration Test - Closed Case",
            "TestInvestigator",
            "This case is currently closed",
            True
        )
        created_ids["closed_case_id"] = closed_case_id

        yield created_ids

    finally:
        if "open_case_id" in created_ids:
            await conn.execute(
                'DELETE FROM "Cases_DB"."Cases" WHERE CaseId = $1',
                uuid.UUID(created_ids["open_case_id"])
            )
        if "closed_case_id" in created_ids:
            await conn.execute(
                'DELETE FROM "Cases_DB"."Cases" WHERE CaseId = $1',
                uuid.UUID(created_ids["closed_case_id"])
            )
        await conn.close()

@pytest.mark.asyncio
async def test_integration_get_cases_investigator(client, fake_get_cases_context):
    
    mock_investigator_user = {
        "id": str(uuid.uuid4()),
        "username": "test_investigator",
        "role": "INVESTIGATOR"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_investigator_user))

    response = client.post("/api/getCases", json={})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    returned_case_ids = [c["caseId"] for c in data["cases"]]

    assert fake_get_cases_context["open_case_id"] in returned_case_ids
    assert fake_get_cases_context["closed_case_id"] in returned_case_ids

@pytest.mark.asyncio
async def test_integration_get_cases_regular_user(client, fake_get_cases_context):

    mock_regular_user = {
        "id": str(uuid.uuid4()),
        "username": "test_user",
        "role": "USER"
    }
    client.cookies.set(COOKIE_NAME, create_token(mock_regular_user))

    response = client.post("/api/getCases", json={})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    returned_case_ids = [c["caseId"] for c in data["cases"]]

    assert fake_get_cases_context["closed_case_id"] in returned_case_ids
    assert fake_get_cases_context["open_case_id"] not in returned_case_ids

@pytest.mark.asyncio
async def test_integration_get_cases_unauthorized(client):

    client.cookies.clear()

    response = client.request("POST", "/api/getCases")

    assert response.status_code == 401
    assert response.json()["detail"]["status"] == "error"
import json
import uuid
import asyncpg
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.api.main import app
from app.auth.auth import COOKIE_NAME, create_token
from app.core.env import Postgres_Settings, User_Settings
from app.tests.integration.conftest import get_connection

USER_SETTINGS = User_Settings()


@pytest_asyncio.fixture
async def fake_case_board_context(ensure_user_exists):
    conn = await get_connection()
    created_ids = {}
    user_id = "9b74b4e3-7823-464b-a65f-4df2d75eeab3"

    try:
        await ensure_user_exists(conn, user_id, "TestInvest", "INVESTIGATOR")

        async with conn.transaction():
            await conn.execute(f"SET LOCAL app.current_user_id = '{user_id}';")

            case_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO "Cases_DB"."Cases" 
                (CaseId, CaseName, CaseCreator, CaseDescription, CaseState)
                VALUES ($1, $2, $3, $4, $5::case_state_enum)
                """,
                uuid.UUID(case_id),
                "Integration Test Case Board Case",
                "CaseCreator",
                "Integration test case description",
                "OPEN",
            )
            created_ids["case_id"] = case_id

            await conn.execute(
                """
                UPDATE "Cases_DB"."Cases"
                SET CaseAssigned = $2,
                    CaseState = 'PUBLISHED'::case_state_enum
                WHERE CaseId = $1
                """,
                uuid.UUID(case_id),
                "TestInvest",
            )

        yield {"case_id": case_id}

    finally:
        async with conn.transaction():
            await conn.execute(f"SET LOCAL app.current_user_id = '{user_id}';")

            if "case_id" in created_ids:
                await conn.execute(
                    """DELETE FROM "Cases_DB"."CaseBoard" 
                    WHERE CaseId = $1""",
                    uuid.UUID(created_ids["case_id"]),
                )
                await conn.execute(
                    """DELETE FROM "Cases_DB"."Cases" 
                    WHERE CaseId = $1""",
                    uuid.UUID(created_ids["case_id"]),
                )

        await conn.close()


async def check_case_board(case_id, expected_case_board=None):
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            """
            SELECT CaseBoard
            FROM "Cases_DB"."CaseBoard"
            WHERE CaseId = $1
            """,
            uuid.UUID(case_id),
        )

        if expected_case_board is None:
            assert row is None, f"Unexpected case board row found for case {case_id}."
            return

        assert row is not None, f"Case board for case {case_id} not found in database."

        db_case_board = row["caseboard"]

        if isinstance(db_case_board, str):
            db_case_board = json.loads(db_case_board)
        assert db_case_board == expected_case_board

    finally:
        await conn.close()


# Test for the 200
@pytest.mark.asyncio
async def test_integration_save_case_board_success(client, fake_case_board_context):
    case_id = fake_case_board_context["case_id"]
    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "INVESTIGATOR",
    }

    test_token = create_token(mock_invest)
    client.cookies.set(COOKIE_NAME, test_token)

    payload = {
        "caseId": case_id,
        "caseBoard": {
            "nodes": [
                {
                    "id": "1",
                    "type": "note",
                    "text": "Suspect vehicle",
                },
                {
                    "id": "2",
                    "type": "evidence",
                    "text": "Fingerprint match",
                },
            ],
            "edges": [
                {
                    "from": "1",
                    "to": "2",
                }
            ],
        },
    }

    response = client.post("/api/saveCaseBoard", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "success"

    await check_case_board(case_id, payload["caseBoard"])


# Test the update overwrites a previously saved board rather than duplicating it
@pytest.mark.asyncio
async def test_integration_save_case_board_overwrites_existing(client, fake_case_board_context):
    case_id = fake_case_board_context["case_id"]
    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "INVESTIGATOR",
    }

    test_token = create_token(mock_invest)
    client.cookies.set(COOKIE_NAME, test_token)

    first_payload = {
        "caseId": case_id,
        "caseBoard": {
            "nodes": [
                {
                    "id": "1",
                    "type": "note",
                    "text": "First draft",
                }
            ],
            "edges": [],
        },
    }
    second_payload = {
        "caseId": case_id,
        "caseBoard": {
            "nodes": [
                {
                    "id": "1",
                    "type": "note",
                    "text": "Updated draft",
                }
            ],
            "edges": [],
        },
    }

    response = client.post("/api/saveCaseBoard", json=first_payload)
    assert response.status_code == 200

    response = client.post("/api/saveCaseBoard", json=second_payload)
    assert response.status_code == 200

    await check_case_board(case_id, second_payload["caseBoard"])


# Test 401, Invalid UUID
@pytest.mark.asyncio
async def test_integration_save_case_board_invalid_uuid(client, fake_case_board_context):
    case_id = fake_case_board_context["case_id"]

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "INVESTIGATOR",
    }

    test_token = create_token(mock_invest)
    client.cookies.set(COOKIE_NAME, test_token)

    payload = {
        "caseId": "Invalid UUID",
        "caseBoard": {
            "nodes": [
                {
                    "id": "1",
                    "type": "note",
                    "text": "Suspect vehicle",
                }
            ],
            "edges": [],
        },
    }

    response = client.post("/api/saveCaseBoard", json=payload)

    assert response.status_code == 401
    assert response.json()["detail"]["status"] == "error"

    await check_case_board(case_id)


# Test 401, Invalid JWT
@pytest.mark.asyncio
async def test_integration_save_case_board_invalid_jwt(client, fake_case_board_context):
    case_id = fake_case_board_context["case_id"]

    test_token = ""
    client.cookies.set(COOKIE_NAME, test_token)

    payload = {
        "caseId": case_id,
        "caseBoard": {
            "nodes": [
                {
                    "id": "1",
                    "type": "note",
                    "text": "Suspect vehicle",
                }
            ],
            "edges": [],
        },
    }

    response = client.post("/api/saveCaseBoard", json=payload)

    assert response.status_code == 401
    assert response.json()["detail"]["status"] == "error"

    await check_case_board(case_id)


# 403 - User doesn't have permission. Role is USER
@pytest.mark.asyncio
async def test_integration_save_case_board_user_unauthorized(client, fake_case_board_context):
    case_id = fake_case_board_context["case_id"]

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "USER",
    }

    test_token = create_token(mock_invest)
    client.cookies.set(COOKIE_NAME, test_token)

    payload = {
        "caseId": case_id,
        "caseBoard": {
            "nodes": [
                {
                    "id": "1",
                    "type": "note",
                    "text": "Suspect vehicle",
                }
            ],
            "edges": [],
        },
    }

    response = client.post("/api/saveCaseBoard", json=payload)

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"

    await check_case_board(case_id)

# 403 - Investigator/admin is not the assignee of the case
@pytest.mark.asyncio
async def test_integration_save_case_board_unassigned_investigator_forbidden(
    client, fake_case_board_context, ensure_user_exists
):
    case_id = fake_case_board_context["case_id"]

    other_user_id = "1c2d3e4f-5678-4abc-9def-0123456789ab"
    conn = await get_connection()
    try:
        await ensure_user_exists(conn, other_user_id, "OtherInvest", "INVESTIGATOR")
    finally:
        await conn.close()

    mock_invest = {
        "id": other_user_id,
        "username": "OtherInvest",
        "role": "INVESTIGATOR",
    }

    test_token = create_token(mock_invest)
    client.cookies.set(COOKIE_NAME, test_token)

    payload = {
        "caseId": case_id,
        "caseBoard": {
            "nodes": [
                {
                    "id": "1",
                    "type": "note",
                    "text": "Suspect vehicle",
                }
            ],
            "edges": [],
        },
    }

    response = client.post("/api/saveCaseBoard", json=payload)

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"

    await check_case_board(case_id)


@pytest_asyncio.fixture
async def seeded_case_board(fake_case_board_context):
    case_id = fake_case_board_context["case_id"]
    user_id = "9b74b4e3-7823-464b-a65f-4df2d75eeab3"

    board_data = {
        "nodes": [
            {
                "id": "1",
                "type": "note",
                "text": "Fixture seeded board",
            }
        ],
        "edges": [],
    }

    conn = await get_connection()
    try:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO "Cases_DB"."CaseBoard" (CaseId, CaseBoard)
                VALUES ($1, $2::jsonb)
                ON CONFLICT (CaseId) DO UPDATE SET CaseBoard = EXCLUDED.CaseBoard;
                """,
                uuid.UUID(case_id),
                json.dumps(board_data),
            )
    finally:
        await conn.close()
    return {
        "case_id": case_id,
        "user_id": user_id,
        "board_data": board_data,
    }


@pytest.mark.asyncio
async def test_integration_get_case_board_success(client, seeded_case_board):
    case_id = seeded_case_board["case_id"]

    mock_invest = {
        "id": seeded_case_board["user_id"],
        "username": "TestInvest",
        "role": "INVESTIGATOR",
    }
    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.get(f"/api/getCaseBoard/{case_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["caseId"] == case_id
    assert data["caseBoard"] == seeded_case_board["board_data"]
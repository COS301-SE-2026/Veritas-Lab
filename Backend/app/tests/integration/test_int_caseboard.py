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
    
    # 1. Distinct Investigator 
    invest_id = str(uuid.uuid4())
    base_invest = "invest"
    invest_name = f"{base_invest}_{invest_id[:8]}"
    
    # 2. Distinct Creator
    creator_id = str(uuid.uuid4())
    base_creator = "creator"
    creator_name = f"{base_creator}_{creator_id[:8]}"

    try:
        # Create investigator and update role explicitly
        await ensure_user_exists(conn, invest_id, base_invest)
        await conn.execute('UPDATE "Users_DB"."Users" SET userrole = $1 WHERE userid = $2::uuid', 'INVESTIGATOR', invest_id)
        
        # Create creator and update role explicitly
        await ensure_user_exists(conn, creator_id, base_creator)
        await conn.execute('UPDATE "Users_DB"."Users" SET userrole = $1 WHERE userid = $2::uuid', 'USER', creator_id)

        async with conn.transaction():
            # Set the local user context for the audit logs
            await conn.execute(f"SET LOCAL app.current_user_id = '{creator_id}';")

            case_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO "Cases_DB"."Cases" 
                (CaseId, CaseName, CaseCreator, CaseDescription, CaseState)
                VALUES ($1, $2, $3, $4, $5::case_state_enum)
                """,
                uuid.UUID(case_id),
                "Integration Test Case Board Case",
                creator_name, # Created by the user
                "Integration test case description",
                "OPEN",
            )
            created_ids["case_id"] = case_id

            await conn.execute(f"SET LOCAL app.current_user_id = '{invest_id}';")
            await conn.execute(
                """
                UPDATE "Cases_DB"."Cases"
                SET CaseAssigned = $2,
                    CaseState = 'PUBLISHED'::case_state_enum
                WHERE CaseId = $1
                """,
                uuid.UUID(case_id),
                invest_name, # Assigned to the investigator
            )

        yield {"case_id": case_id, "user_id": invest_id, "username": invest_name}

    finally:
        async with conn.transaction():
            await conn.execute(f"SET LOCAL app.current_user_id = '{invest_id}';")

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
        "id": fake_case_board_context["user_id"],
        "username": fake_case_board_context["username"],
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
        "id": fake_case_board_context["user_id"],
        "username": fake_case_board_context["username"],
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


# Test 400, Invalid UUID
@pytest.mark.asyncio
async def test_integration_save_case_board_invalid_uuid(client, fake_case_board_context):
    case_id = fake_case_board_context["case_id"]

    mock_invest = {
        "id": fake_case_board_context["user_id"],
        "username": fake_case_board_context["username"],
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
async def test_integration_save_case_board_user_unauthorized(client, fake_case_board_context, ensure_user_exists):
    case_id = fake_case_board_context["case_id"]

    conn = await get_connection()
    user_id = str(uuid.uuid4())
    base_name = "testuser"
    username = f"{base_name}_{user_id[:8]}"
    try:
        await ensure_user_exists(conn, user_id, base_name)
        await conn.execute('UPDATE "Users_DB"."Users" SET userrole = $1 WHERE userid = $2::uuid', 'USER', user_id)
    finally:
        await conn.close()

    mock_user = {
        "id": user_id,
        "username": username,
        "role": "USER",
    }

    test_token = create_token(mock_user)
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

    other_user_id = str(uuid.uuid4())
    base_other = "otherinv"
    other_username = f"{base_other}_{other_user_id[:8]}"
    
    conn = await get_connection()
    try:
        await ensure_user_exists(conn, other_user_id, base_other)
        await conn.execute('UPDATE "Users_DB"."Users" SET userrole = $1 WHERE userid = $2::uuid', 'INVESTIGATOR', other_user_id)
    finally:
        await conn.close()

    mock_invest = {
        "id": other_user_id,
        "username": other_username,
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
    user_id = fake_case_board_context["user_id"]
    username = fake_case_board_context["username"]

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
        "username": username,
        "board_data": board_data,
    }


@pytest.mark.asyncio
async def test_integration_get_case_board_success(client, seeded_case_board):
    case_id = seeded_case_board["case_id"]

    mock_invest = {
        "id": seeded_case_board["user_id"],
        "username": seeded_case_board["username"],
        "role": "INVESTIGATOR",
    }
    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.get(f"/api/CaseBoard/{case_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["caseId"] == case_id
    assert data["caseBoard"] == seeded_case_board["board_data"]

@pytest.mark.asyncio
async def test_integration_get_case_board_none_returns_null(client, fake_case_board_context):
    case_id = fake_case_board_context["case_id"]

    mock_invest = {
        "id": fake_case_board_context["user_id"],
        "username": fake_case_board_context["username"],
        "role": "INVESTIGATOR",
    }
    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.get(f"/api/CaseBoard/{case_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["caseId"] == case_id
    assert data["caseBoard"] is None

@pytest.mark.asyncio
async def test_integration_get_case_board_invalid_uuid(client, ensure_user_exists):
    conn = await get_connection()
    user_id = str(uuid.uuid4())
    base_name = "testinvest"
    username = f"{base_name}_{user_id[:8]}"
    try:
        await ensure_user_exists(conn, user_id, base_name)
        await conn.execute('UPDATE "Users_DB"."Users" SET userrole = $1 WHERE userid = $2::uuid', 'INVESTIGATOR', user_id)
    finally:
        await conn.close()

    mock_invest = {
        "id": user_id,
        "username": username,
        "role": "INVESTIGATOR",
    }
    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.get("/api/CaseBoard/invalid-uuid-string")

    assert response.status_code == 400
    assert response.json()["detail"]["status"] == "error"

@pytest.mark.asyncio
async def test_integration_get_case_board_invalid_jwt(client, seeded_case_board):
    case_id = seeded_case_board["case_id"]

    client.cookies.set(COOKIE_NAME, "")

    response = client.get(f"/api/CaseBoard/{case_id}")

    assert response.status_code == 401
    assert response.json()["detail"]["status"] == "error"
    
@pytest.mark.asyncio
async def test_integration_get_case_board_user_unauthorized(client, seeded_case_board, ensure_user_exists):
    case_id = seeded_case_board["case_id"]

    conn = await get_connection()
    user_id = str(uuid.uuid4())
    base_name = "testuser"
    username = f"{base_name}_{user_id[:8]}"
    try:
        await ensure_user_exists(conn, user_id, base_name)
        await conn.execute('UPDATE "Users_DB"."Users" SET userrole = $1 WHERE userid = $2::uuid', 'USER', user_id)
    finally:
        await conn.close()

    mock_user = {
        "id": user_id,
        "username": username,
        "role": "USER",
    }
    client.cookies.set(COOKIE_NAME, create_token(mock_user))

    response = client.get(f"/api/CaseBoard/{case_id}")

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"

@pytest.mark.asyncio
async def test_integration_get_case_board_not_found(client, ensure_user_exists):
    non_existent_case_id = str(uuid.uuid4())

    conn = await get_connection()
    user_id = str(uuid.uuid4())
    base_name = "testinvest"
    username = f"{base_name}_{user_id[:8]}"
    try:
        await ensure_user_exists(conn, user_id, base_name)
        await conn.execute('UPDATE "Users_DB"."Users" SET userrole = $1 WHERE userid = $2::uuid', 'INVESTIGATOR', user_id)
    finally:
        await conn.close()

    mock_invest = {
        "id": user_id,
        "username": username,
        "role": "INVESTIGATOR",
    }
    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.get(f"/api/CaseBoard/{non_existent_case_id}")

    assert response.status_code == 404
    assert response.json()["detail"]["status"] == "error"
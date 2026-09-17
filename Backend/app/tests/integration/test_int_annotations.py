# Test 200 that annotations are saved
# Test 401 the invalid JWT and Invalid UUID
# Test 403 the unauthorised user

import pytest
from fastapi.testclient import TestClient
from app.api.main import app
from app.core.env import User_Settings, Postgres_Settings
import pytest_asyncio
import asyncpg
import json
import uuid
from app.auth.auth import create_token, COOKIE_NAME 
from app.tests.integration.conftest import get_connection

USER_SETTINGS = User_Settings()


@pytest_asyncio.fixture
async def fake_annotation_context(ensure_user_exists):
    conn = await get_connection()
    created_ids = {}
    user_id = "9b74b4e3-7823-464b-a65f-4df2d75eeab3"

    try:
        await ensure_user_exists(conn, user_id, "TestInvest", "INVESTIGATOR")

        async with conn.transaction():

            await conn.execute(f"SET LOCAL app.current_user_id = '{user_id}';")

            media_type_id = str(uuid.uuid4())
            media_name = f"IMAGE_PNG_"
            
            await conn.execute(
                """
                INSERT INTO "Cases_DB"."MediaType" 
                (MediaTypeId, MediaName, MediaBucket, MediaExtension)
                VALUES ($1, $2, $3, $4)
                """,
                uuid.UUID(media_type_id), 
                media_name, 
                "test-bucket", 
                ".tester"
            )
            created_ids["media_type_id"] = media_type_id

            media_id = str(uuid.uuid4())
            media_hash = f"{uuid.uuid4().hex}"

            await conn.execute(
                """
                INSERT INTO "Cases_DB"."Media" 
                (MediaId, MediaType, MediaHash)
                VALUES ($1, $2, $3)
                """,
                uuid.UUID(media_id), 
                uuid.UUID(media_type_id), 
                media_hash
            )
            created_ids["media_id"] = media_id

            case_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO "Cases_DB"."Cases" 
                (CaseId, CaseName, CaseCreator, CaseDescription, CaseState)
                VALUES ($1, $2, $3, $4, $5::case_state_enum)
                """,
                uuid.UUID(case_id), 
                "Integration Test Investigation Case",
                "CaseCreator",
                "Integration test case description", 
                "OPEN",
            )
            created_ids["case_id"] = case_id

            await conn.execute(
                """
                UPDATE "Cases_DB"."Cases"
                SET CaseAssigned = $2,
                    CaseState = 'PUBLISHED'::case_state_enum,
                    evidence = ARRAY[
                        ROW($3, $4)::"Cases_DB".evidence_type
                    ]
                WHERE CaseId = $1
                """,
                uuid.UUID(case_id),
                "TestInvest",
                uuid.UUID(media_id),
                "annotation evidence"
            )

        yield {"case_id": case_id, "media_id": media_id}

    finally:
        async with conn.transaction():
            await conn.execute(f"SET LOCAL app.current_user_id = '{user_id}';")

            if "case_id" in created_ids:
                await conn.execute(
                    """DELETE FROM "Cases_DB"."Cases" 
                    WHERE CaseId = $1""",
                    uuid.UUID(created_ids["case_id"])
                )

            if "media_id" in created_ids:
                await conn.execute(
                    """DELETE FROM "Cases_DB"."Media" 
                    WHERE MediaId = $1""",
                    uuid.UUID(created_ids["media_id"])
                )

            if "media_type_id" in created_ids:
                await conn.execute(
                    """DELETE FROM "Cases_DB"."MediaType" 
                    WHERE MediaTypeId = $1""",
                    uuid.UUID(created_ids["media_type_id"])
                )

        await conn.close()

async def check_annotations(media_id, expected_annotations=None):
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            """
            SELECT MediaAnnotations
            FROM "Cases_DB"."Media"
            WHERE MediaId = $1
            """,
            uuid.UUID(media_id)
        )

        assert row is not None, f"Media {media_id} not found in database."

        db_annotations = row["mediaannotations"]

        if isinstance(db_annotations, str):
            db_annotations = json.loads(db_annotations)
        assert db_annotations == expected_annotations

    finally:
        await conn.close()
    

# Test for the 200
@pytest.mark.asyncio
async def test_integration_save_annotations_success(client, fake_annotation_context):
    case_id = fake_annotation_context["case_id"]
    media_id = fake_annotation_context["media_id"]
    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "INVESTIGATOR"
    }

    test_token = create_token(mock_invest)
    client.cookies.set(COOKIE_NAME, test_token)

    payload = {
        "caseId": case_id,
        "mediaId": media_id,
        "annotations": [
            {
                "type": "bounding_box", 
                "coordinates": [10, 20, 100, 200], 
                "label": "evidence"
            },
            {
                "type": "line",
                "coordinates": [0, 0, 100, 100],
                "label": "underline_1"
            }
        ]
    }

    response = client.post(
        "/api/saveAnnotations",
        json=payload
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"

    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            """
            SELECT MediaAnnotations
            FROM "Cases_DB"."Media"
            WHERE MediaId = $1
            """,
            uuid.UUID(media_id)
        )

        assert row is not None, f"Media {media_id} not found in database."

        db_annotations = row["mediaannotations"]

        if isinstance(db_annotations, str):
            db_annotations = json.loads(db_annotations)

        assert db_annotations == payload["annotations"]
        assert len(db_annotations) == 2
        assert db_annotations[0]["label"] == "evidence"

    finally:
        await conn.close()

# Test 401, Invalid UUID
@pytest.mark.asyncio
async def test_integration_save_annotations_invalid_uuid(client, fake_annotation_context):
    case_id = fake_annotation_context["case_id"]
    media_id = fake_annotation_context["media_id"]

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "INVESTIGATOR"
    }

    test_token = create_token(mock_invest)
    client.cookies.set(COOKIE_NAME, test_token)

    payload = {
        "caseId": "Invalid UUID",
        "mediaId": media_id,
        "annotations": [
            {
                "type": "line", 
                "coordinates": [10, 20, 100, 200], 
                "label": "scribble"
            },
            {
                "type": "highlight",
                "coordinates": [0, 0, 100, 100],
                "label": "power"
            }
        ]
    }

    response = client.post(
        "/api/saveAnnotations",
        json=payload
    )

    assert response.status_code == 401
    assert response.json()["detail"]["status"] == "error"

    await check_annotations(media_id)

# Test 401, Invalid JWT
@pytest.mark.asyncio
async def test_integration_save_annotations_invalid_jwt(client, fake_annotation_context):
    case_id = fake_annotation_context["case_id"]
    media_id = fake_annotation_context["media_id"]

    test_token = ""
    client.cookies.set(COOKIE_NAME, test_token)

    payload = {
        "caseId": case_id,
        "mediaId": media_id,
        "annotations": [
            {
                "type": "line", 
                "coordinates": [10, 20, 100, 200], 
                "label": "scribble"
            },
            {
                "type": "highlight",
                "coordinates": [0, 0, 100, 100],
                "label": "power"
            }
        ]
    }

    response = client.post(
        "/api/saveAnnotations",
        json=payload
    )

    assert response.status_code == 401
    assert response.json()["detail"]["status"] == "error"

    await check_annotations(media_id)

# 403 - User doesn't have permission. Role is USER
@pytest.mark.asyncio
async def test_integration_save_annotations_user_unauthorized(client, fake_annotation_context):
    case_id = fake_annotation_context["case_id"]
    media_id = fake_annotation_context["media_id"]

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "USER"
    }

    test_token = create_token(mock_invest)
    client.cookies.set(COOKIE_NAME, test_token)

    payload = {
        "caseId": case_id,
        "mediaId": media_id,
        "annotations": [
            {
                "type": "line", 
                "coordinates": [10, 20, 100, 200], 
                "label": "Pasco"
            },
            {
                "type": "highlight",
                "coordinates": [0, 0, 100, 100],
                "label": "powerm2"
            }
        ]
    }

    response = client.post(
        "/api/saveAnnotations",
        json=payload
    )

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"

    await check_annotations(media_id)

@pytest_asyncio.fixture
async def fake_comment_context(ensure_user_exists):
    conn = await get_connection()
    created_ids = {}
    user_id = "9b74b4e3-7823-464b-a65f-4df2d75eeab3"

    try:
        await ensure_user_exists(conn, user_id, "TestInvest", "INVESTIGATOR")

        async with conn.transaction():

            await conn.execute(f"SET LOCAL app.current_user_id = '{user_id}';")
            case_id1 = str(uuid.uuid4())
            case_creation_literal = """
            INSERT INTO "Cases_DB"."Cases" 
            (CaseId, CaseName, 
            CaseCreator, CaseDescription, CaseState)
            VALUES ($1, $2, $3, $4, $5::case_state_enum)
            """

            await conn.execute(
                case_creation_literal,
                uuid.UUID(case_id1), 
                "Test Case", "Creator",
                "To test comments", 
                "OPEN"
            )

            created_ids["case_id1"] = case_id1

            case_id2 = str(uuid.uuid4())
            await conn.execute(
                case_creation_literal,
                uuid.UUID(case_id2), 
                "Test separation", 
                "TestInvest", 
                "For more Tests", 
                "OPEN"
            )
            created_ids["case_id2"] = case_id2

            comment_creation_literal = """
            INSERT INTO "Cases_DB"."Comments" (CaseId, Username, Comment)
            VALUES ($1, $2, $3)
            RETURNING CommentID
            """

            comment_1_user = "Creator"
            comment_1_comment = "Checking if you receive this message"
            row = await conn.fetchrow(
                comment_creation_literal,
                uuid.UUID(case_id1),
                comment_1_user,
                comment_1_comment
            )
            comment_id1 = row["commentid"]

            comment_2_comment = "Nothing"
            comment_2_user = "TestInvest"
            row = await conn.fetchrow(
                comment_creation_literal,
                uuid.UUID(case_id1),
                comment_2_user,
                comment_2_comment
            )
            comment_id2 = row["commentid"]

        yield {
            "case_id1": case_id1,
            "case_id2": case_id2,
            "comment_id1": comment_id1,
            "comment_1_user": comment_1_user,
            "comment_1_comment": comment_1_comment,
            "comment_id2": comment_id2,
            "comment_2_user": comment_2_user,
            "comment_2_comment": comment_2_comment,
        }

    finally:
        async with conn.transaction():
            await conn.execute(f"SET LOCAL app.current_user_id = '{user_id}';")
            delete_case = """
            DELETE FROM "Cases_DB"."Cases" WHERE CaseId = $1
            """
            if "case_id1" in created_ids:
                await conn.execute(
                    delete_case,
                    uuid.UUID(created_ids["case_id1"])
                )
            if "case_id2" in created_ids:
                await conn.execute(
                    delete_case,
                    uuid.UUID(created_ids["case_id2"])
                )
        await conn.close()


# - 200: Ideal
@pytest.mark.asyncio
async def test_integration_get_comment_multiple_success(client, fake_comment_context):
    case_id = fake_comment_context["case_id1"]

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "INVESTIGATOR"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.post(f"/api/getComments/{case_id}")

    assert response.status_code == 200
    assert response.json()["status"] == "success"

    assert len(response.json()["comments"]) == 2
    first_comment = response.json()["comments"][0]

    assert first_comment["commentid"] == fake_comment_context["comment_id1"]
    assert first_comment["username"] == fake_comment_context["comment_1_user"]
    assert first_comment["comment"] == fake_comment_context["comment_1_comment"]

    second_comment = response.json()["comments"][1]

    assert second_comment["commentid"] == fake_comment_context["comment_id2"]
    assert second_comment["username"] == fake_comment_context["comment_2_user"]
    assert second_comment["comment"] == fake_comment_context["comment_2_comment"]
    
@pytest.mark.asyncio
async def test_integration_get_comment_empty_success(client, fake_comment_context):
    case_id = fake_comment_context["case_id2"]

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "INVESTIGATOR"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.post(f"/api/getComments/{case_id}")

    assert response.status_code == 200
    assert response.json()["status"] == "success"

    assert len(response.json()["comments"]) == 0
    
# - 400: invalid uuid
@pytest.mark.asyncio
async def test_integration_get_comment_invalid_id_format_error(client, fake_comment_context):
    case_id = "13"

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "INVESTIGATOR"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.post(f"/api/getComments/{case_id}")

    assert response.status_code == 400
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] == "'13' is not a valid UUID format"


# - 404: Missing report id
@pytest.mark.asyncio
async def test_integration_get_comment_missing_id_error(client, fake_comment_context):
    case_id = ""

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "INVESTIGATOR"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.post(f"/api/getComments/{case_id}")

    assert response.status_code == 404


# - 401: The JWT errors. (Missing)
@pytest.mark.asyncio
async def test_integration_get_comment_missing_cookie_error(client, fake_comment_context):
    case_id = fake_comment_context["case_id1"]

    mock_invest = ""

    client.cookies.set(COOKIE_NAME, mock_invest)

    response = client.post(f"/api/getComments/{case_id}")

    assert response.status_code == 401
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] == "Not authenticated"


# - 403: A normal user tries to get comments
@pytest.mark.asyncio
async def test_integration_get_comment_invalid_cookie_error(client, fake_comment_context):
    case_id = fake_comment_context["case_id1"]

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "USER"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.post(f"/api/getComments/{case_id}")

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] == "User unauthorized"

# 201
@pytest.mark.asyncio
async def test_integration_create_comment_success(client, fake_comment_context):
    case_id = fake_comment_context["case_id1"]
    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "INVESTIGATOR"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))
    comment = "Help me tests my limits"
    payload = {
        "case_id": case_id,
        "comment": comment
    }
    response = client.post(
        "/api/cases/comments",
        json=payload
    )

    assert response.status_code == 201
    assert response.json()["status"] == "success"
    response_data = response.json()["comment"]
    assert response_data["comment"] == comment
    assert response_data["username"] == "TestInvest"

    comment_id = response_data["commentId"]

    conn = await get_connection()
    try:
        db_row = await conn.fetchrow(
            'SELECT * FROM "Cases_DB"."Comments" WHERE CommentId = $1',
            comment_id
        )
        
        assert db_row is not None, f"There doesn't exist a {comment_id} comment in the database."

        assert db_row["comment"] == comment
        assert db_row["username"] == "TestInvest"
        assert str(db_row["caseid"]) == case_id
        
    finally:
        await conn.close()

async def assert_against_comment_table(user_name):
    conn = await get_connection()
    try:
        db_row = await conn.fetchrow(
            'SELECT * FROM "Cases_DB"."Comments" WHERE Username = $1',
            user_name
        )
        
        assert db_row is None, f"There exists a comment in the database from {user_name}."
    finally:
        await conn.close()

# 400
@pytest.mark.asyncio
async def test_integration_create_comment_empty_string(client, fake_comment_context):
    case_id = fake_comment_context["case_id1"]
    user_name = "MRBeast"
    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": user_name,
        "role": "INVESTIGATOR"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))
    comment = ""
    payload = {
        "case_id": case_id,
        "comment": comment
    }
    response = client.post(
        "/api/cases/comments",
        json=payload
    )

    assert response.status_code == 400
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] == "Comment must be a non-empty string"
    await assert_against_comment_table(user_name)

@pytest.mark.asyncio
async def test_integration_create_comment_invalid_case_id(client, fake_comment_context):
    case_id = ""
    user_name = "MRBeast"
    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": user_name,
        "role": "INVESTIGATOR"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))
    comment = "Beans"
    payload = {
        "case_id": case_id,
        "comment": comment
    }
    response = client.post(
        "/api/cases/comments",
        json=payload
    )

    assert response.status_code == 422
    await assert_against_comment_table(user_name)

# 403
@pytest.mark.asyncio
async def test_integration_create_comment_invalid_role(client, fake_comment_context):
    case_id = fake_comment_context["case_id1"]
    user_name = "MRBeast"
    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": user_name,
        "role": "Fred"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))
    comment = "Good day"
    payload = {
        "case_id": case_id,
        "comment": comment
    }
    response = client.post(
        "/api/cases/comments",
        json=payload
    )

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] == "Permission denied"
    await assert_against_comment_table(user_name)

@pytest.mark.asyncio
async def test_integration_create_comment_user_open_case_forbidden(client, fake_comment_context):
    case_id = fake_comment_context["case_id1"]
    user_name = "MRBeast"
    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": user_name,
        "role": "USER"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))
    comment = "Good day"
    payload = {
        "case_id": case_id,
        "comment": comment
    }
    response = client.post(
        "/api/cases/comments",
        json=payload
    )

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] == "Users may only comment on closed cases"
    await assert_against_comment_table(user_name)

# 404
@pytest.mark.asyncio
async def test_integration_create_comment_case_not_found(client, fake_comment_context):
    case_id = "2e067604-67c0-4b56-aeab-ca92e702aeb6"
    user_name = "MRBeast"
    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": user_name,
        "role": "INVESTIGATOR"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))
    comment = "Good day"
    payload = {
        "case_id": case_id,
        "comment": comment
    }
    response = client.post(
        "/api/cases/comments",
        json=payload
    )

    assert response.status_code == 404
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] == "Case not found"
    await assert_against_comment_table(user_name)
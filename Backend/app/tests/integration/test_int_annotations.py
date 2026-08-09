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

USER_SETTINGS=User_Settings()
POSTGRES_SEETTINGS=Postgres_Settings()

async def get_connection() -> asyncpg.Connection:
    return await asyncpg.connect(
        user=POSTGRES_SEETTINGS.DB_USER,
        password=POSTGRES_SEETTINGS.DB_PASSWORD,
        database=POSTGRES_SEETTINGS.DB_NAME,
        host=POSTGRES_SEETTINGS.DB_HOST,
        port=POSTGRES_SEETTINGS.DB_PORT,
        ssl="require" if POSTGRES_SEETTINGS.DB_SSL else None,
    )

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest_asyncio.fixture
async def fake_report_context():
    conn = await get_connection()
    created_ids = {}

    try:
        media_type_id = str(uuid.uuid4())
        media_name = f"IMAGE_PNG_"
        
        await conn.execute(
            """
            INSERT INTO "Cases_DB"."MediaType" (MediaTypeId, MediaName, MediaBucket, MediaExtension)
            VALUES ($1, $2, $3, $4)
            """,
            uuid.UUID(media_type_id), media_name, "test-bucket", ".tester"
        )
        created_ids["media_type_id"] = media_type_id

        media_id = str(uuid.uuid4())
        media_hash = f"{uuid.uuid4().hex}"

        await conn.execute(
            """
            INSERT INTO "Cases_DB"."Media" (MediaId, MediaType, MediaHash)
            VALUES ($1, $2, $3)
            """,
            uuid.UUID(media_id), uuid.UUID(media_type_id), media_hash
        )
        created_ids["media_id"] = media_id

        case_id = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO "Cases_DB"."Cases" (CaseId, CaseName, CaseCreator, CaseDescription, CaseClosed)
            VALUES ($1, $2, $3, $4, $5)
            """,
            uuid.UUID(case_id), "Integration Test Investigation Case", "TestInvest", "Integration test case description", False
        )
        created_ids["case_id"] = case_id

        report_row = await conn.fetchrow(
            """
            INSERT INTO "Cases_DB"."Reports" 
            (CaseId, MediaId, ImageTitle )
            VALUES ($1, $2, $3)
            RETURNING ReportId, CaseId, MediaId, ImageTitle
            """,
            uuid.UUID(case_id),
            uuid.UUID(media_id),
            media_name
        )

        report_id = str(report_row["reportid"])
        created_ids["report_id"] = report_id

        yield report_id 

    finally:
        if "case_id" in created_ids:
            await conn.execute(
                'DELETE FROM "Cases_DB"."Cases" WHERE CaseId = $1',
                uuid.UUID(created_ids["case_id"])
            )

        if "media_id" in created_ids:
            await conn.execute(
                'DELETE FROM "Cases_DB"."Media" WHERE MediaId = $1',
                uuid.UUID(created_ids["media_id"])
            )

        if "media_type_id" in created_ids:
            await conn.execute(
                'DELETE FROM "Cases_DB"."MediaType" WHERE MediaTypeId = $1',
                uuid.UUID(created_ids["media_type_id"])
            )

        await conn.close()

async def check_annotations(payload, report_id):
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            """
            SELECT m.MediaAnnotations 
            FROM "Cases_DB"."Reports" r
            JOIN "Cases_DB"."Media" m ON r.MediaId = m.MediaId
            WHERE r.ReportId = $1
            """,
            uuid.UUID(report_id)
        )

        assert row is not None, f"Report {report_id} not found in database."

        db_annotations = row["mediaannotations"]

        if db_annotations is not None:
            if isinstance(db_annotations, str):
                db_annotations = json.loads(db_annotations)
            assert db_annotations != payload["annotations"]
        else:
            assert db_annotations is None

    finally:
        await conn.close()
    

# Test for the 200
@pytest.mark.asyncio
async def test_integration_save_annotations_success(client, fake_report_context):
    report_id = fake_report_context
    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "INVESTIGATOR"
    }

    test_token=create_token(mock_invest)
    client.cookies.set(COOKIE_NAME, test_token)

    payload={
        "reportId": report_id,
        "annotations": [
            {
                "type": "bounding_box", 
                "coordinates": [10, 20, 100, 200], 
                "label": "evidence"
            },
            {
                "type":"line",
                "coordinates": [0,0,100,100],
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
            SELECT m.MediaAnnotations
            FROM "Cases_DB"."Reports" r
            JOIN "Cases_DB"."Media" m ON r.MediaId = m.MediaId
            WHERE r.ReportId = $1
            """,
            uuid.UUID(report_id)
        )

        assert row is not None, f"Report {report_id} not found in database."

        db_annotations = row["mediaannotations"]

        if isinstance(db_annotations, str):
            db_annotations = json.loads(db_annotations)

        assert db_annotations == payload["annotations"]
        assert len(db_annotations) == 2
        assert db_annotations[0]["label"] == "evidence"

    finally:
        await conn.close()

#Test 401, Invalid UUID
@pytest.mark.asyncio
async def test_integration_save_annotations_invalid_uuid(client, fake_report_context):
    report_id = fake_report_context

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "INVESTIGATOR"
    }

    test_token=create_token(mock_invest)
    client.cookies.set(COOKIE_NAME, test_token)

    payload={
        "reportId": "Invalid UUID",
        "annotations": [
            {
                "type": "line", 
                "coordinates": [10, 20, 100, 200], 
                "label": "scribble"
            },
            {
                "type":"highlight",
                "coordinates": [0,0,100,100],
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

    await check_annotations(payload,report_id)

#Test 401, Invalid JWT
@pytest.mark.asyncio
async def test_integration_save_annotations_invalid_jwt(client, fake_report_context):
    report_id = fake_report_context

    test_token=""
    client.cookies.set(COOKIE_NAME, test_token)

    payload={
        "reportId": report_id,
        "annotations": [
            {
                "type": "line", 
                "coordinates": [10, 20, 100, 200], 
                "label": "scribble"
            },
            {
                "type":"highlight",
                "coordinates": [0,0,100,100],
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

    await check_annotations(payload,report_id)

#403- User doesn't have permission. The role is User or anything but the ADMIN or INVESTIGATOR
@pytest.mark.asyncio
async def test_integration_save_annotations_invalid_uuid(client, fake_report_context):
    report_id = fake_report_context

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "USER"
    }

    test_token=create_token(mock_invest)
    client.cookies.set(COOKIE_NAME, test_token)

    payload={
        "reportId": "Invalid UUID",
        "annotations": [
            {
                "type": "line", 
                "coordinates": [10, 20, 100, 200], 
                "label": "Pasco"
            },
            {
                "type":"highlight",
                "coordinates": [0,0,100,100],
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

    await check_annotations(payload,report_id)
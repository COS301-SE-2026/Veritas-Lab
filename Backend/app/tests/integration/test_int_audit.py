import uuid

import pytest
import pytest_asyncio

from app.auth.auth import COOKIE_NAME, create_token
from app.tests.integration.conftest import get_connection

INVESTIGATOR =  "Audit_Investigator"
ADMIN = "Audit_Admin"

@pytest_asyncio.fixture
async def audit_context(ensure_user_exists):
    conn = await get_connection()
    investigator_id = str(uuid.uuid4())
    admin_id = str(uuid.uuid4())

    await ensure_user_exists(conn, investigator_id, INVESTIGATOR, "INVESTIGATOR")
    await ensure_user_exists(conn, admin_id, ADMIN, "ADMIN")

    investigator_name = f"{INVESTIGATOR}_{investigator_id[:8]}"
    admin_name = f"{ADMIN}_{admin_id[:8]}"
    created_case_ids = []

    try:
        yield {
            "conn": conn,
            "investigator_id": investigator_id,
            "investigator_name": investigator_name,
            "investigator_token": create_token(
                {"id": investigator_id, "username": INVESTIGATOR, "role": "INVESTIGATOR"}
            ),
            "admin_token": create_token(
                {"id": admin_id, "username": ADMIN, "role": "ADMIN"}
            ),
            "cases": created_case_ids,
        }
    finally:
        await conn.execute(
            "SELECT set_config('app.current_user_id', $1, false)", investigator_id
        )
        for case_id in created_case_ids:
            rows = await conn.fetch(
                'SELECT mediaid FROM "Cases_DB"."Reports" WHERE caseid = $1',
                uuid.UUID(case_id),
            )
            await conn.execute(
                'DELETE FROM "Cases_DB"."Cases" WHERE caseid = $1', uuid.UUID(case_id)
            )
            for row in rows:
                await conn.execute(
                    'DELETE FROM "Cases_DB"."Media" WHERE mediaid = $1', row["mediaid"]
                )
    await conn.close()

async def seed_case(ctx, closed=False):
    conn = ctx["conn"]
    case_id = uuid.uuid4()
    await conn.execute(
        "SELECT set_config('app.current_user_id', $1, false)", ctx["investigator_id"]
    )
    await conn.execute(
        """
        INSERT INTO "Cases_DB"."Cases" 
        (CaseId, CaseName, CaseCreator, CaseDescription, CaseClosed)
        VALUES ($1, $2, $3, $4, $5)
        """,
        case_id, "Audit test case", ctx["investigator_id"], "This is a test case for auditing.", closed
    )
    ctx["cases"].append(str(case_id))
    return str(case_id)

async def seed_evidence(ctx, case_id):
    conn = ctx["conn"]
    media_type = await conn.fetchval(
        'SELECT mediatypeid FROM "Cases_DB"."MediaType" WHERE mediaextension = $1', ".png"
    )
    media_id = uuid.uuid4()
    await conn.execute(
        'INSERT INTO "Cases_DB"."Media" (MediaId, MediaType, MediaHash) VALUES ($1, $2, $3)',
        media_id, media_type, uuid.uuid4().hex,
    )
    await conn.execute(
        'INSERT INTO "Cases_DB"."Reports" (CaseId, MediaId, ImageTitle) VALUES ($1, $2, $3)',
        case_id, media_id, "Test Evidence",
    )
    return media_id

def actions(events):
    #since the endpoint returns newest first, we then read the oldest by reversing the list
    return [event["action"] for event in reversed(events.json()["events"])]

@pytest.mark.asyncio
async def test_case_lifecycle_actions(client, audit_context):
    ctx = audit_context
    conn = ctx["conn"]
    case_id = await seed_case(ctx)

    await conn.execute(
        'UPDATE "Cases_DB"."Cases" SET casename = $2 WHERE CaseId = $1',
        case_id, "Renamed Case"
    )
    await conn.execute(
        'UPDATE "Cases_DB"."Cases" SET casedescription = $2 WHERE CaseId = $1',
        case_id, "Updated description"
    )
    await conn.execute(
        'UPDATE "Cases_DB"."Cases" SET caseclosed = TRUE WHERE CaseId = $1',
        case_id
    )

    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])
    response = client.get(f"/api/getAudit/caseID/{case_id}")
    
    assert response.status_code == 200, response.text
    assert actions(response) == [
        "Case Created",
        "Case Renamed",
        "Case Description Updated",
        "Case Closed",
    ]
    assert all(event["user"] == ctx["investigator_name"] for event in response.json()["events"])

@pytest.mark.asyncio
async def test_case_deletion_is_recorded(client, audit_context):
    ctx = audit_context
    case_id = await seed_case(ctx)

    await ctx["conn"].execute(
        'DELETE FROM "Cases_DB"."Cases" WHERE CaseId = $1', case_id
    )
    ctx["cases"].remove(case_id)

    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])
    response = client.get(f"/api/getAudit/caseID/{case_id}")

    assert response.status_code == 200, response.text
    assert actions(response) == ["Case Created", "Case Deleted"]

@pytest.mark.asyncio
async def test_evidence_added_and_annotated(client, audit_context):
    ctx = audit_context
    case_id = await seed_case(ctx)
    media_id = await seed_evidence(ctx, case_id)

    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])
    assert "Evidence Added" in actions(client.get(f"/api/getAudit/caseID/{case_id}"))

    await ctx["conn"].execute(
        'UPDATE "Cases_DB"."Media" SET mediaannotations = $2::jsonb WHERE MediaId = $1',
        media_id, '[{"box": [0,0,10,10]}]',
    )

    assert "Evidence Annotated" in actions(client.get(f"/api/getAudit/caseID/{case_id}"))

#This test ensures that when evidence is removed, it does not create an audit event for "Evidence Removed". 
#The audit trail should only record the addition and annotation of evidence, not its removal.
@pytest.mark.asyncio
async def test_evidence_removal_is_not_recorded(client, audit_context):
    ctx = audit_context
    case_id = await seed_case(ctx)
    media_id = await seed_evidence(ctx, case_id)

    await ctx["conn"].execute(
        'DELETE FROM "Cases_DB"."Reports" WHERE mediaid = $1', media_id
    )

    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])
    result = actions(client.get(f"/api/getAudit/caseID/{case_id}"))

    assert "Evidence Removed" not in result
    assert "Evidence Added" not in result

@pytest.mark.asyncio
async def test_timeline_empty_for_unaudited_case(client, audit_context):
    client.cookies.set(COOKIE_NAME, audit_context["investigator_token"])
    response = client.get(f"/api/getAudit/caseID/{uuid.uuid4()}")

    assert response.status_code == 200, response.text
    assert response.json()["events"] == []

@pytest.mark.asyncio
async def test_timeline_requires_authentication(client, audit_context):
    client.cookies.clear()
    response = client.get(f"/api/getAudit/caseID/{uuid.uuid4()}")

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_all_audited_cases(client, audit_context):
    ctx = audit_context
    await seed_case(ctx)

    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])
    assert client.get("/api/getAllAudit").status_code == 403


    client.cookies.set(COOKIE_NAME, ctx["admin_token"])
    response = client.get("/api/getAllAudit")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "success"
    assert set(body["cases"][0]) == {
        "caseId", "caseName", "eventCount", "lastEventTimestamp", "caseExists"
    }

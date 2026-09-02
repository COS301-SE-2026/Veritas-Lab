import uuid

import pytest
import pytest_asyncio

from app.auth.auth import COOKIE_NAME, create_token
from app.core.media_relay import MediaRelay
from app.tests.integration.conftest import get_connection

INVESTIGATOR =  "Audit_Investigator"
ADMIN = "Audit_Admin"

@pytest.fixture(autouse=True)
def stub_media_pipeline(monkeypatch):
    async def no_op(self):
        return None
    
    monkeypatch.setattr(MediaRelay, "relay_to_service", no_op)

def cookie_for(username: str, role: str, user_id: str) ->str:
    return create_token({"id": user_id, "username": username, "role": role})

def png_bytes() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + uuid.uuid4().hex.encode()

@pytest_asyncio.fixture
async def audit_context(ensure_user_exists):
    conn = await get_connection()
    investigator_id = str(uuid.uuid4())
    admin_id = str(uuid.uuid4())

    await ensure_user_exists(conn, investigator_id, INVESTIGATOR, "INVESTIGATOR")
    await ensure_user_exists(conn, admin_id, ADMIN, "ADMIN")

    created_case_ids = []

    try:
        yield {
            "conn": conn,
            "investigator_id": investigator_id,
            "investigator_name": f"{INVESTIGATOR}_{investigator_id[:8]}",
            "admin_id": admin_id,
            "admin_name": f"{ADMIN}_{admin_id[:8]}",
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

def _login(client, ctx, role="INVESTIGATOR"):
    if role == "ADMIN":
        client.cookies.set(
            COOKIE_NAME, cookie_for(ctx["admin_name"], "ADMIN", ctx["admin_id"])
        )
    else:
        client.cookies.set(
            COOKIE_NAME,
            cookie_for(ctx["investigator_name"], "INVESTIGATOR", ctx["investigator_id"]),
        )

def _create_case(client, ctx, title="Audit timeline case"):
    response = client.post(
        "/api/createCase",
        json={"title": title, "description": "Testfor audit"},
    )
    assert response.status_code == 201, response.text
    case_id = str(response.json()["CaseId"])
    ctx["cases"].append(case_id)
    return case_id

def _timeline(client, case_id):
    response = client.get(f"/api/getAudit/caseID/{case_id}")
    assert response.status_code == 200, response.text
    return response.json()["events"]

def _actions(events):
    #since the endpoint returns newest first, we then read the oldest by reversing the list
    return [event["action"] for event in reversed(events)]

@pytest.mark.asyncio
async def test_case_lifecycle_actions(client, audit_context):
    ctx = audit_context
    _login(client, ctx)

    case_id = _create_case(client, ctx)

    rename = client.post(
        f"/api/updateCase", json={"CaseID": case_id, "CaseName": "Renamed Case"}
    )
    assert rename.status_code == 200, rename.text

    describe = client.post(
        f"/api/updateCase",
        json={"CaseID": case_id, "CaseDescription": "Updated description"}
    )
    assert describe.status_code == 200, describe.text

    close = client.post("/api/closeCase", json={"CaseID": case_id})
    assert close.status_code == 200, close.text

    events = _timeline(client, case_id)

    assert _actions(events) == [
        "Case Created",
        "Case Renamed",
        "Case Description Updated",
        "Case Closed",
    ]
    assert all(event["user"] == ctx["investigator_name"] for event in events)

@pytest.mark.asyncio
async def test_case_deletion_is_recorded(client, audit_context):
    ctx = audit_context
    _login(client, ctx)

    case_id = _create_case(client, ctx)

    delete = client.request("DELETE", "/api/deleteCase", json={"CaseID": case_id})
    assert delete.status_code == 200, delete.text
    ctx["cases"].remove(case_id)

    assert _actions(_timeline(client, case_id)) == ["Case Created", "Case Deleted"]

@pytest.mark.asyncio
async def test_evidence_added_and_annotated(client, audit_context):
    ctx = audit_context
    _login(client, ctx)

    case_id = _create_case(client, ctx)

    # Add evidence
    upload = client.post(
        "/api/cases/evidence",
        data={"case_id": case_id},
        files={"media": ("evidence.png", png_bytes(), "image/png")},
    )
    assert upload.status_code == 201, upload.text
    media_id = upload.json()["evidence"]["MediaId"]

    assert "Evidence Added" in _actions(_timeline(client, case_id))

    conn = ctx["conn"]
    report_id = await conn.fetchval(
        'SELECT reportid FROM "Cases_DB"."Reports" WHERE mediaid = $1',
        uuid.UUID(media_id),
    )

    annotate = client.post(
        "/api/saveAnnotations",
        json={"reportId": str(report_id), "annotations": [{"boxes": []}]},
    )

    assert annotate.status_code == 200, annotate.text
    assert "Evidence Annotated" in _actions(_timeline(client, case_id))

#This test ensures that when evidence is removed, it does not create an audit event for "Evidence Removed". 
#The audit trail should only record the addition and annotation of evidence, not its removal.
@pytest.mark.asyncio
async def test_evidence_removal_is_not_recorded(client, audit_context):
    ctx = audit_context
    _login(client, ctx)

    case_id = _create_case(client, ctx)

    # Add evidence
    upload = client.post(
        "/api/cases/evidence",
        data={"case_id": case_id},
        files={"media": ("evidence.png", png_bytes(), "image/png")},
    )
    assert upload.status_code == 201, upload.text
    media_id = upload.json()["evidence"]["MediaId"]

    assert "Evidence Added" in _actions(_timeline(client, case_id))

    # Remove evidence
    remove = client.delete(
        "/api/cases/evidence",
        json={"case_id": case_id, "media_id": media_id},
    )
    assert remove.status_code == 200, remove.text

    # Ensure that the removal is not recorded in the audit timeline
    actions = _actions(_timeline(client, case_id))
    assert "Evidence Removed" not in actions
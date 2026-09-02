import uuid

import pytest
import pytest_asyncio

from.app.auth.auth import COOKIE_NAME, create_token
from app.core.media_relay import MediaRelay
from app.tests.integration.conftest import get_connection

INVESTIGATOR =  "Audit_Investigator"
AMIN = "Audit_Admin"

@pyetes.fixture(autouse=True)
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
            "created_case_ids": created_case_ids,
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
                'DELETE FROM "Cases_DB"."Reports" WHERE caseid = $1', uuid.UUID(case_id)
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

def _create_case(client, ctx, title="Test Case", description="Test Description"):
    response = client.post(
        "/api/createCase",
        json={"title": title, "description": description},
    )
    assert response.status_code == 201, resposne.text
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


import uuid

import pytest
import pytest_asyncio

from app.auth.auth import COOKIE_NAME, create_token
from app.tests.integration.conftest import get_connection

INVESTIGATOR = "Assign_Investigator"
ADMIN = "Assign_Admin"
CREATOR = "Assign_Creator"
USER = "Assign_User"

@pytest_asyncio.fixture
async def assign_context(ensure_user_exists):
    conn = await get_connection()

    investigator_id = str(uuid.uuid4())
    admin_id = str(uuid.uuid4())
    creator_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    await ensure_user_exists(
        conn,
        investigator_id,
        INVESTIGATOR,
        "INVESTIGATOR"
    )

    await ensure_user_exists(
        conn,
        admin_id,
        ADMIN,
        "ADMIN"
    )

    await ensure_user_exists(
        conn,
        creator_id,
        CREATOR,
        "USER"
    )

    await ensure_user_exists(
        conn,
        user_id,
        USER,
        "USER"
    )

    created_case_ids = []

    try:
        yield {
            "conn": conn,

            "investigator_id": investigator_id,
            "investigator_token": create_token(
                {
                    "id": investigator_id,
                    "username": INVESTIGATOR,
                    "role": "INVESTIGATOR"
                }
            ),

            "admin_id": admin_id,
            "admin_token": create_token(
                {
                    "id": admin_id,
                    "username": ADMIN,
                    "role": "ADMIN"
                }
            ),

            "creator_id": creator_id,
            "creator_token": create_token(
                {
                    "id": creator_id,
                    "username": CREATOR,
                    "role": "USER"
                }
            ),

            "user_token": create_token(
                {
                    "id": user_id,
                    "username": USER,
                    "role": "USER"
                }
            ),

            "cases": created_case_ids,
        }

    finally:
        for case_id in created_case_ids:
            await conn.execute(
                """
                DELETE FROM "Cases_DB"."Cases"
                WHERE caseid = $1
                """,
                uuid.UUID(case_id)
            )

        await conn.close()

async def seed_case(
    ctx,
    state="PUBLISHED",
    creator=CREATOR,
    assigned=None
):
    conn = ctx["conn"]
    case_id = uuid.uuid4()

    await conn.execute(
        """
        INSERT INTO "Cases_DB"."Cases"
            (
                caseid,
                casename,
                casecreator,
                casedescription,
                casestate,
                caseassigned
            )
        VALUES (
            $1,
            $2,
            $3,
            $4,
            $5::case_state_enum,
            $6
        )
        """,
        case_id,
        "Assignment test case",
        creator,
        "Case used for investigator assignment testing",
        state,
        assigned
    )

    ctx["cases"].append(str(case_id))
    return str(case_id)

@pytest.mark.asyncio
async def test_investigator_can_assign_published_case(client, assign_context):
    ctx = assign_context
    case_id = await seed_case(ctx)
    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])

    response = client.patch(
        "/api/assignCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "status": "success",
        "message": "Case assigned successfully"
    }

    assigned = await ctx["conn"].fetchval(
        """
        SELECT caseassigned
        FROM "Cases_DB"."Cases"
        WHERE caseid = $1
        """,
        uuid.UUID(case_id)
    )

    assert assigned == INVESTIGATOR

@pytest.mark.asyncio
async def test_admin_can_assign_published_case(client, assign_context):
    ctx = assign_context
    case_id = await seed_case(ctx)
    client.cookies.set(COOKIE_NAME, ctx["admin_token"])

    response = client.patch(
        "/api/assignCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 200, response.text

    assigned = await ctx["conn"].fetchval(
        """
        SELECT caseassigned
        FROM "Cases_DB"."Cases"
        WHERE caseid = $1
        """,
        uuid.UUID(case_id)
    )

    assert assigned == ADMIN

@pytest.mark.asyncio
async def test_user_cannot_assign_case(client, assign_context):
    ctx = assign_context
    case_id = await seed_case(ctx)
    client.cookies.set(COOKIE_NAME, ctx["user_token"])

    response = client.patch(
        "/api/assignCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"] == {
        "status": "error",
        "message": "User unauthorized"
    }

    assigned = await ctx["conn"].fetchval(
        """
        SELECT caseassigned
        FROM "Cases_DB"."Cases"
        WHERE caseid = $1
        """,
        uuid.UUID(case_id)
    )

    assert assigned is None

@pytest.mark.asyncio
async def test_cannot_assign_open_case(client, assign_context):
    ctx = assign_context
    case_id = await seed_case(ctx, state="OPEN")

    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])
    response = client.patch(
        "/api/assignCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "status": "error",
        "message": "Invalid assignment request"
    }

    assigned = await ctx["conn"].fetchval(
        """
        SELECT caseassigned
        FROM "Cases_DB"."Cases"
        WHERE caseid = $1
        """,
        uuid.UUID(case_id)
    )

    assert assigned is None

@pytest.mark.asyncio
async def test_cannot_assign_already_assigned_case(client, assign_context):
    ctx = assign_context
    case_id = await seed_case(ctx)

    await ctx["conn"].execute(
        """
        UPDATE "Cases_DB"."Cases"
        SET caseassigned = $2
        WHERE caseid = $1
        """,
        uuid.UUID(case_id),
        ADMIN
    )

    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])

    response = client.patch(
        "/api/assignCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 400

    assigned = await ctx["conn"].fetchval(
        """
        SELECT caseassigned
        FROM "Cases_DB"."Cases"
        WHERE caseid = $1
        """,
        uuid.UUID(case_id)
    )

    assert assigned == ADMIN

@pytest.mark.asyncio
async def test_investigator_cannot_assign_own_case(client, assign_context):
    ctx = assign_context
    case_id = await seed_case(ctx, creator=INVESTIGATOR)
    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])

    response = client.patch(
        "/api/assignCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "status": "error",
        "message": "Invalid assignment request"
    }

    assigned = await ctx["conn"].fetchval(
        """
        SELECT caseassigned
        FROM "Cases_DB"."Cases"
        WHERE caseid = $1
        """,
        uuid.UUID(case_id)
    )

    assert assigned is None

@pytest.mark.asyncio
async def test_assign_case_requires_case_id(client, assign_context):
    ctx = assign_context
    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])

    response = client.patch(
        "/api/assignCase",
        json={
            "CaseID": None
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "status": "error",
        "message": "CaseID required"
    }

@pytest.mark.asyncio
async def test_assign_case_requires_authentication(client, assign_context):
    case_id = await seed_case(assign_context)
    client.cookies.clear()

    response = client.patch(
        "/api/assignCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 401
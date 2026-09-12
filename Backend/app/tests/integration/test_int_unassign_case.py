import uuid

import pytest
import pytest_asyncio

from app.auth.auth import COOKIE_NAME, create_token
from app.tests.integration.conftest import get_connection

INVESTIGATOR = "Unassign_Investigator"
ADMIN = "Unassign_Admin"
OTHER_INVESTIGATOR = "Other_Investigator"
CREATOR = "Unassign_Creator"
USER = "Unassign_User"

@pytest_asyncio.fixture
async def unassign_context(ensure_user_exists):
    conn = await get_connection()

    investigator_id = str(uuid.uuid4())
    admin_id = str(uuid.uuid4())
    other_investigator_id = str(uuid.uuid4())
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
        other_investigator_id,
        OTHER_INVESTIGATOR,
        "INVESTIGATOR"
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

            "other_investigator_id": other_investigator_id,
            "other_investigator_token": create_token(
                {
                    "id": other_investigator_id,
                    "username": OTHER_INVESTIGATOR,
                    "role": "INVESTIGATOR"
                }
            ),

            "creator_id": creator_id,

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
    creator=CREATOR
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
            casestate
        )
        VALUES (
            $1,
            $2,
            $3,
            $4,
            $5::case_state_enum
        )
        """,
        case_id,
        "Unassignment test case",
        creator,
        "Case used for unassignment testing",
        state
    )

    ctx["cases"].append(str(case_id))
    return str(case_id)

async def assign_case_to(ctx, case_id, username, executor_id):
    await ctx["conn"].execute(
        "SELECT set_config('app.current_user_id', $1, false)",
        executor_id
    )

    await ctx["conn"].execute(
        """
        UPDATE "Cases_DB"."Cases"
        SET caseassigned = $2
        WHERE caseid = $1
        """,
        uuid.UUID(case_id),
        username
    )

@pytest.mark.asyncio
async def test_investigator_can_unassign_themselves(client, unassign_context):
    ctx = unassign_context

    case_id = await seed_case(ctx)

    await assign_case_to(
        ctx,
        case_id,
        INVESTIGATOR,
        ctx["investigator_id"]
    )

    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])

    response = client.patch(
        "/api/unassignCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "status": "success",
        "message": "Case unassigned successfully"
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
async def test_admin_can_unassign_themselves(client, unassign_context):
    ctx = unassign_context
    case_id = await seed_case(ctx)

    await assign_case_to(
        ctx,
        case_id,
        ADMIN,
        ctx["admin_id"]
    )

    client.cookies.set(COOKIE_NAME, ctx["admin_token"])

    response = client.patch(
        "/api/unassignCase",
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

    assert assigned is None

@pytest.mark.asyncio
async def test_user_cannot_unassign_case(client, unassign_context):
    ctx = unassign_context

    case_id = await seed_case(ctx)

    await assign_case_to(
        ctx,
        case_id,
        INVESTIGATOR,
        ctx["investigator_id"]
    )

    client.cookies.set(COOKIE_NAME, ctx["user_token"])

    response = client.patch(
        "/api/unassignCase",
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

    assert assigned == INVESTIGATOR

@pytest.mark.asyncio
async def test_investigator_cannot_unassign_other_investigator(client, unassign_context):
    ctx = unassign_context
    case_id = await seed_case(ctx)

    await assign_case_to(
        ctx,
        case_id,
        OTHER_INVESTIGATOR,
        ctx["other_investigator_id"]
    )

    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])

    response = client.patch(
        "/api/unassignCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 400

    assert response.json()["detail"] == {
        "status": "error",
        "message": "Invalid unassignment request"
    }

    assigned = await ctx["conn"].fetchval(
        """
        SELECT caseassigned
        FROM "Cases_DB"."Cases"
        WHERE caseid = $1
        """,
        uuid.UUID(case_id)
    )

    assert assigned == OTHER_INVESTIGATOR

@pytest.mark.asyncio
async def test_cannot_unassign_unassigned_case(client, unassign_context):
    ctx = unassign_context
    case_id = await seed_case(ctx)
    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])

    response = client.patch(
        "/api/unassignCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 400

    assert response.json()["detail"] == {
        "status": "error",
        "message": "Invalid unassignment request"
    }

@pytest.mark.asyncio
async def test_cannot_unassign_open_case(client, unassign_context):
    ctx = unassign_context
    case_id = await seed_case(ctx, state="OPEN")

    await assign_case_to(
        ctx,
        case_id,
        INVESTIGATOR,
        ctx["investigator_id"]
    )

    client.cookies.set(
        COOKIE_NAME,
        ctx["investigator_token"]
    )

    response = client.patch(
        "/api/unassignCase",
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

    assert assigned == INVESTIGATOR

@pytest.mark.asyncio
async def test_unassign_case_requires_case_id(client, unassign_context):
    ctx = unassign_context
    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])

    response = client.patch(
        "/api/unassignCase",
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
async def test_unassign_case_requires_authentication(client, unassign_context):
    ctx = unassign_context
    case_id = await seed_case(ctx)
    client.cookies.clear()

    response = client.patch(
        "/api/unassignCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 401
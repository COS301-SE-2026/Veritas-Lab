import uuid
import pytest
from app.auth.auth import COOKIE_NAME

async def seed_case(
    ctx,
    state="PUBLISHED",
    creator=None
):
    conn = ctx["conn"]
    case_id = uuid.uuid4()

    if creator is None:
        creator = ctx["creator_name"]

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
        "Close test case",
        creator,
        "Case used for close-case integration testing",
        state
    )

    ctx["cases"].append(str(case_id))

    return str(case_id)


async def assign_case_to(
    ctx,
    case_id,
    username,
    executor_id
):
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
async def test_investigator_can_close_assigned_published_case(client, case_assignment_context):
    ctx = case_assignment_context
    case_id = await seed_case(ctx)

    await assign_case_to(
        ctx,
        case_id,
        ctx["investigator_name"],
        ctx["investigator_id"]
    )

    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])

    response = client.patch(
        "/api/closeCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "status": "success",
        "message": "Case closed successfully."
    }

    row = await ctx["conn"].fetchrow(
        """
        SELECT casestate, caseclosedate
        FROM "Cases_DB"."Cases"
        WHERE caseid = $1
        """,
        uuid.UUID(case_id)
    )

    assert row["casestate"] == "CLOSED"
    assert row["caseclosedate"] is not None


@pytest.mark.asyncio
async def test_admin_can_close_assigned_published_case(client, case_assignment_context):
    ctx = case_assignment_context
    case_id = await seed_case(ctx)

    await assign_case_to(
        ctx,
        case_id,
        ctx["admin_name"],
        ctx["admin_id"]
    )

    client.cookies.set(COOKIE_NAME, ctx["admin_token"])

    response = client.patch(
        "/api/closeCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 200, response.text

    state = await ctx["conn"].fetchval(
        """
        SELECT casestate
        FROM "Cases_DB"."Cases"
        WHERE caseid = $1
        """,
        uuid.UUID(case_id)
    )

    assert state == "CLOSED"

@pytest.mark.asyncio
async def test_user_cannot_close_case(client, case_assignment_context):
    ctx = case_assignment_context
    case_id = await seed_case(ctx)

    await assign_case_to(
        ctx,
        case_id,
        ctx["investigator_name"],
        ctx["investigator_id"]
    )

    client.cookies.set(
        COOKIE_NAME,
        ctx["user_token"]
    )

    response = client.patch(
        "/api/closeCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 403

    assert response.json()["detail"] == {
        "status": "error",
        "message": "User unauthorized"
    }

    state = await ctx["conn"].fetchval(
        """
        SELECT casestate
        FROM "Cases_DB"."Cases"
        WHERE caseid = $1
        """,
        uuid.UUID(case_id)
    )

    assert state == "PUBLISHED"

@pytest.mark.asyncio
async def test_investigator_cannot_close_case_assigned_to_someone_else(client, case_assignment_context):
    ctx = case_assignment_context
    case_id = await seed_case(ctx)

    await assign_case_to(
        ctx,
        case_id,
        ctx["other_investigator_name"],
        ctx["other_investigator_id"]
    )

    client.cookies.set(
        COOKIE_NAME,
        ctx["investigator_token"]
    )

    response = client.patch(
        "/api/closeCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 404

    state = await ctx["conn"].fetchval(
        """
        SELECT casestate
        FROM "Cases_DB"."Cases"
        WHERE caseid = $1
        """,
        uuid.UUID(case_id)
    )

    assert state == "PUBLISHED"

@pytest.mark.asyncio
async def test_cannot_close_open_case(client, case_assignment_context):
    ctx = case_assignment_context
    case_id = await seed_case(ctx, state="OPEN")

    await assign_case_to(
        ctx,
        case_id,
        ctx["investigator_name"],
        ctx["investigator_id"]
    )

    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])

    response = client.patch(
        "/api/closeCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 404

    row = await ctx["conn"].fetchrow(
        """
        SELECT casestate, caseclosedate
        FROM "Cases_DB"."Cases"
        WHERE caseid = $1
        """,
        uuid.UUID(case_id)
    )

    assert row["casestate"] == "OPEN"
    assert row["caseclosedate"] is None

@pytest.mark.asyncio
async def test_cannot_close_unassigned_case(client, case_assignment_context):
    ctx = case_assignment_context
    case_id = await seed_case(ctx)
    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])

    response = client.patch(
        "/api/closeCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 404

    state = await ctx["conn"].fetchval(
        """
        SELECT casestate
        FROM "Cases_DB"."Cases"
        WHERE caseid = $1
        """,
        uuid.UUID(case_id)
    )

    assert state == "PUBLISHED"

@pytest.mark.asyncio
async def test_close_case_requires_case_id(client, case_assignment_context):
    ctx = case_assignment_context
    client.cookies.set(
        COOKIE_NAME,
        ctx["investigator_token"]
    )

    response = client.patch(
        "/api/closeCase",
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
async def test_close_case_requires_authentication(client, case_assignment_context):
    ctx = case_assignment_context
    case_id = await seed_case(ctx)

    client.cookies.clear()

    response = client.patch(
        "/api/closeCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 401
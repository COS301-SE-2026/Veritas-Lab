import uuid
import pytest
import pytest_asyncio

from app.auth.auth import COOKIE_NAME, create_token
from app.tests.integration.conftest import get_connection

USER = "Publish_User"
INVESTIGATOR = "Publish_Investigator"
ADMIN = "Publish_Admin"
OTHER_USER = "Publish_Other_User"

@pytest_asyncio.fixture
async def publish_context(ensure_user_exists):
    conn = await get_connection()

    user_id = str(uuid.uuid4())
    investigator_id = str(uuid.uuid4())
    admin_id = str(uuid.uuid4())
    other_user_id = str(uuid.uuid4())

    user_name = await ensure_user_exists(
        conn,
        user_id,
        USER,
        "USER"
    )

    investigator_name = await ensure_user_exists(
        conn,
        investigator_id,
        INVESTIGATOR,
        "INVESTIGATOR"
    )

    admin_name = await ensure_user_exists(
        conn,
        admin_id,
        ADMIN,
        "ADMIN"
    )

    other_user_name = await ensure_user_exists(
        conn,
        other_user_id,
        OTHER_USER,
        "USER"
    )

    created_case_ids = []

    try:
        yield {
            "conn": conn,

            "user_id": user_id,
            "user_name": user_name,
            "user_token": create_token(
                {
                    "id": user_id,
                    "username": user_name,
                    "role": "USER"
                }
            ),

            "investigator_id": investigator_id,
            "investigator_name": investigator_name,
            "investigator_token": create_token(
                {
                    "id": investigator_id,
                    "username": investigator_name,
                    "role": "INVESTIGATOR"
                }
            ),

            "admin_id": admin_id,
            "admin_name": admin_name,
            "admin_token": create_token(
                {
                    "id": admin_id,
                    "username": admin_name,
                    "role": "ADMIN"
                }
            ),

            "other_user_id": other_user_id,
            "other_user_name": other_user_name,
            "other_user_token": create_token(
                {
                    "id": other_user_id,
                    "username": other_user_name,
                    "role": "USER"
                }
            ),

            "cases": created_case_ids,
        }

    finally:
        await conn.execute(
            "SELECT set_config('app.current_user_id', $1, false)",
            user_id
        )

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
    creator=None,
    creator_id=None,
    state="OPEN"
):
    conn = ctx["conn"]
    creator = creator or ctx["user_name"]
    case_id = uuid.uuid4()

    if creator_id is None:
        creator_id = ctx["user_id"]

    await conn.execute(
        "SELECT set_config('app.current_user_id', $1, false)",
        creator_id
    )

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
        "Publish test case",
        creator,
        "Case used for publish endpoint integration testing",
        state
    )

    ctx["cases"].append(str(case_id))

    return str(case_id)

@pytest.mark.asyncio
async def test_user_can_publish_own_open_case(client, publish_context):
    ctx = publish_context

    case_id = await seed_case(
        ctx,
        creator=ctx["user_name"],
        creator_id=ctx["user_id"]
    )

    client.cookies.set(COOKIE_NAME, ctx["user_token"])

    response = client.patch(
        "/api/publishCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 200, response.text

    assert response.json() == {
        "status": "success",
        "message": "Case published successfully"
    }

    row = await ctx["conn"].fetchrow(
        """
        SELECT casestate, casepublishdate
        FROM "Cases_DB"."Cases"
        WHERE caseid = $1
        """,
        uuid.UUID(case_id)
    )

    assert row["casestate"] == "PUBLISHED"
    assert row["casepublishdate"] is not None

@pytest.mark.asyncio
async def test_investigator_can_publish_own_open_case(client, publish_context):
    ctx = publish_context
    case_id = await seed_case(
        ctx,
        creator=ctx["investigator_name"],
        creator_id=ctx["investigator_id"]
    )

    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])

    response = client.patch(
        "/api/publishCase",
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

    assert state == "PUBLISHED"

@pytest.mark.asyncio
async def test_admin_can_publish_own_open_case(client, publish_context):
    ctx = publish_context
    case_id = await seed_case(
        ctx,
        creator=ctx["admin_name"],
        creator_id=ctx["admin_id"]
    )

    client.cookies.set(COOKIE_NAME, ctx["admin_token"])

    response = client.patch(
        "/api/publishCase",
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

    assert state == "PUBLISHED"

@pytest.mark.asyncio
async def test_user_cannot_publish_another_users_case(client, publish_context):
    ctx = publish_context
    case_id = await seed_case(
        ctx,
        creator=ctx["other_user_name"],
        creator_id=ctx["other_user_id"]
    )

    client.cookies.set(COOKIE_NAME, ctx["user_token"])

    response = client.patch(
        "/api/publishCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 400

    assert response.json()["detail"] == {
        "status": "error",
        "message": "Invalid publish request"
    }

    row = await ctx["conn"].fetchrow(
        """
        SELECT casestate, casepublishdate
        FROM "Cases_DB"."Cases"
        WHERE caseid = $1
        """,
        uuid.UUID(case_id)
    )

    assert row["casestate"] == "OPEN"
    assert row["casepublishdate"] is None

@pytest.mark.asyncio
async def test_cannot_publish_already_published_case(client, publish_context):
    ctx = publish_context

    case_id = await seed_case(
        ctx,
        creator=ctx["user_name"],
        creator_id=ctx["user_id"],
        state="PUBLISHED"
    )

    client.cookies.set(COOKIE_NAME, ctx["user_token"])
    response = client.patch(
        "/api/publishCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "status": "error",
        "message": "Invalid publish request"
    }

@pytest.mark.asyncio
async def test_cannot_publish_closed_case(client, publish_context):
    ctx = publish_context

    case_id = await seed_case(
        ctx,
        creator=ctx["user_name"],
        creator_id=ctx["user_id"],
        state="CLOSED"
    )

    client.cookies.set(COOKIE_NAME, ctx["user_token"])

    response = client.patch(
        "/api/publishCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 400

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
async def test_publish_case_requires_case_id(client, publish_context):
    ctx = publish_context

    client.cookies.set(
        COOKIE_NAME,
        ctx["user_token"]
    )

    response = client.patch(
        "/api/publishCase",
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
async def test_publish_case_requires_authentication(client, publish_context):
    ctx = publish_context
    case_id = await seed_case(ctx)
    client.cookies.clear()

    response = client.patch(
        "/api/publishCase",
        json={
            "CaseID": case_id
        }
    )

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_publish_case_rejects_invalid_role(client, publish_context):
    ctx = publish_context

    case_id = await seed_case(ctx)

    invalid_token = create_token(
        {
            "id": str(uuid.uuid4()),
            "username": "Invalid_Role_User",
            "role": "INVALID_ROLE"
        }
    )

    client.cookies.set(COOKIE_NAME, invalid_token)

    response = client.patch(
        "/api/publishCase",
        json={
            "CaseID": case_id
        }
    )

    # No stored user can hold this role, so the token fails verification before the role check
    assert response.status_code == 401
    assert response.json()["detail"] == {
        "status": "error",
        "message": "Invalid token"
    }
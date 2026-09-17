import pytest
from app.auth.auth import COOKIE_NAME
from app.tests.integration.test_int_get_single_case import seed_case

@pytest.mark.asyncio
async def test_user_receives_own_cases(client, case_assignment_context):
    ctx = case_assignment_context

    own_open = await seed_case(
        ctx,
        creator=ctx["user_name"],
        state="OPEN",
        name="User open case"
    )

    own_published = await seed_case(
        ctx,
        creator=ctx["user_name"],
        state="PUBLISHED",
        name="User published case"
    )

    own_closed = await seed_case(
        ctx,
        creator=ctx["user_name"],
        state="CLOSED",
        name="User closed case"
    )

    client.cookies.set(
        COOKIE_NAME,
        ctx["user_token"]
    )

    response = client.get("/api/getCases")
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["status"] == "success"

    returned_ids = {
        case["caseId"]
        for case in body["cases"]
    }
    assert own_open in returned_ids
    assert own_published in returned_ids
    assert own_closed in returned_ids

@pytest.mark.asyncio
async def test_user_does_not_receive_other_users_cases(client, case_assignment_context):
    ctx = case_assignment_context
    other_open = await seed_case(
        ctx,
        creator=ctx["creator_name"],
        state="OPEN"
    )

    other_published = await seed_case(
        ctx,
        creator=ctx["creator_name"],
        state="PUBLISHED"
    )

    other_closed = await seed_case(
        ctx,
        creator=ctx["creator_name"],
        state="CLOSED"
    )

    client.cookies.set(COOKIE_NAME, ctx["user_token"])
    response = client.get("/api/getCases")

    assert response.status_code == 200, response.text
    returned_ids = {
        case["caseId"]
        for case in response.json()["cases"]
    }

    assert other_open not in returned_ids
    assert other_published not in returned_ids
    assert other_closed not in returned_ids

@pytest.mark.asyncio
async def test_investigator_receives_own_open_case(client, case_assignment_context):
    ctx = case_assignment_context

    own_open = await seed_case(
        ctx,
        creator=ctx["investigator_name"],
        state="OPEN"
    )

    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])
    response = client.get("/api/getCases")

    assert response.status_code == 200, response.text
    returned_ids = {
        case["caseId"]
        for case in response.json()["cases"]
    }

    assert own_open in returned_ids

@pytest.mark.asyncio
async def test_investigator_receives_other_published_and_closed_cases(client, case_assignment_context):
    ctx = case_assignment_context

    published_case = await seed_case(
        ctx,
        creator=ctx["creator_name"],
        state="PUBLISHED"
    )

    closed_case = await seed_case(
        ctx,
        creator=ctx["creator_name"],
        state="CLOSED"
    )

    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])
    response = client.get("/api/getCases")
    assert response.status_code == 200, response.text

    returned_ids = {
        case["caseId"]
        for case in response.json()["cases"]
    }

    assert published_case in returned_ids
    assert closed_case in returned_ids

@pytest.mark.asyncio
async def test_investigator_does_not_receive_other_users_open_case(client, case_assignment_context):
    ctx = case_assignment_context
    open_case = await seed_case(
        ctx,
        creator=ctx["creator_name"],
        state="OPEN"
    )

    client.cookies.set(COOKIE_NAME, ctx["investigator_token"])
    response = client.get("/api/getCases")

    assert response.status_code == 200, response.text
    returned_ids = {
        case["caseId"]
        for case in response.json()["cases"]
    }
    assert open_case not in returned_ids

@pytest.mark.asyncio
async def test_admin_receives_own_open_case(client, case_assignment_context):
    ctx = case_assignment_context
    own_open = await seed_case(
        ctx,
        creator=ctx["admin_name"],
        state="OPEN"
    )

    client.cookies.set(COOKIE_NAME, ctx["admin_token"])
    response = client.get("/api/getCases")
    assert response.status_code == 200, response.text

    returned_ids = {
        case["caseId"]
        for case in response.json()["cases"]
    }
    assert own_open in returned_ids

@pytest.mark.asyncio
async def test_admin_receives_other_published_and_closed_cases(client, case_assignment_context):
    ctx = case_assignment_context

    published_case = await seed_case(
        ctx,
        creator=ctx["creator_name"],
        state="PUBLISHED"
    )

    closed_case = await seed_case(
        ctx,
        creator=ctx["creator_name"],
        state="CLOSED"
    )

    client.cookies.set(COOKIE_NAME, ctx["admin_token"])
    response = client.get("/api/getCases")
    assert response.status_code == 200, response.text

    returned_ids = {
        case["caseId"]
        for case in response.json()["cases"]
    }

    assert published_case in returned_ids
    assert closed_case in returned_ids

@pytest.mark.asyncio
async def test_admin_does_not_receive_other_users_open_case(client, case_assignment_context):
    ctx = case_assignment_context

    open_case = await seed_case(
        ctx,
        creator=ctx["creator_name"],
        state="OPEN"
    )

    client.cookies.set(COOKIE_NAME, ctx["admin_token"])
    response = client.get("/api/getCases")
    assert response.status_code == 200, response.text

    returned_ids = {
        case["caseId"]
        for case in response.json()["cases"]
    }

    assert open_case not in returned_ids

@pytest.mark.asyncio
async def test_get_cases_requires_authentication(client, case_assignment_context):
    client.cookies.clear()
    response = client.get("/api/getCases")
    assert response.status_code == 401
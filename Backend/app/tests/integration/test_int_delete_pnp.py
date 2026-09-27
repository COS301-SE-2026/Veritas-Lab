import pytest
from app.auth.auth import COOKIE_NAME, create_token

@pytest.mark.asyncio
async def test_integration_delete_pnp_investigator_forbidden(client, delete_pnp_context):
    context = delete_pnp_context

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, context["investigator_token"])

    response = client.post(
        "/api/deletePNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "modelName": context["model_name"]
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"

    row = await context["conn"].fetchrow(
        """
        SELECT PNPModelId
        FROM "Cases_DB"."PNPModels"
        WHERE MediaId = $1
        AND ModelName = $2
        """,
        context["media_id"],
        context["model_name"]
    )

    assert row is not None

@pytest.mark.asyncio
async def test_integration_delete_pnp_admin_success(client, delete_pnp_context):
    context = delete_pnp_context

    await context["conn"].execute(
        """
        UPDATE "Cases_DB"."Cases"
        SET CaseAssigned = $1
        WHERE CaseId = $2
        """,
        context["admin_name"],
        context["case_id"]
    )

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, context["admin_token"])

    response = client.post(
        "/api/deletePNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "modelName": context["model_name"]
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"

    row = await context["conn"].fetchrow(
        """
        SELECT PNPModelId
        FROM "Cases_DB"."PNPModels"
        WHERE MediaId = $1
        AND ModelName = $2
        """,
        context["media_id"],
        context["model_name"]
    )

    assert row is None

@pytest.mark.asyncio
async def test_integration_delete_pnp_user_forbidden(client, delete_pnp_context):
    context = delete_pnp_context

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, context["user_token"])

    response = client.post(
        "/api/deletePNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "modelName": context["model_name"]
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"

    row = await context["conn"].fetchrow(
        """
        SELECT PNPModelId
        FROM "Cases_DB"."PNPModels"
        WHERE MediaId = $1
        AND ModelName = $2
        """,
        context["media_id"],
        context["model_name"]
    )

    assert row is not None

@pytest.mark.asyncio
async def test_integration_delete_pnp_unassigned_investigator_forbidden(client, delete_pnp_context):
    context = delete_pnp_context

    other_token = create_token(
        {
            "id": context["other_investigator_id"],
            "username": context["other_investigator_name"],
            "role": "INVESTIGATOR"
        }
    )

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, other_token)

    response = client.post(
        "/api/deletePNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "modelName": context["model_name"]
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"

    row = await context["conn"].fetchrow(
        """
        SELECT PNPModelId
        FROM "Cases_DB"."PNPModels"
        WHERE MediaId = $1
        AND ModelName = $2
        """,
        context["media_id"],
        context["model_name"]
    )

    assert row is not None

@pytest.mark.asyncio
async def test_integration_delete_pnp_wrong_model_name(client, delete_pnp_context):
    context = delete_pnp_context

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, context["investigator_token"])

    response = client.post(
        "/api/deletePNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "modelName": "WrongModel"
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"

    row = await context["conn"].fetchrow(
        """
        SELECT PNPModelId
        FROM "Cases_DB"."PNPModels"
        WHERE MediaId = $1
        AND ModelName = $2
        """,
        context["media_id"],
        context["model_name"]
    )

    assert row is not None

@pytest.mark.asyncio
async def test_integration_delete_pnp_wrong_case(client, delete_pnp_context):
    context = delete_pnp_context

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, context["investigator_token"])

    response = client.post(
        "/api/deletePNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": "33333333-3333-3333-3333-333333333333",
            "modelName": context["model_name"]
        }
    )

    assert response.status_code == 403

    row = await context["conn"].fetchrow(
        """
        SELECT PNPModelId
        FROM "Cases_DB"."PNPModels"
        WHERE MediaId = $1
        AND ModelName = $2
        """,
        context["media_id"],
        context["model_name"]
    )

    assert row is not None

@pytest.mark.asyncio
async def test_integration_delete_pnp_missing_cookie(client, delete_pnp_context):
    context = delete_pnp_context
    client.cookies.clear()

    response = client.post(
        "/api/deletePNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "modelName": context["model_name"]
        }
    )

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_integration_delete_pnp_invalid_token(client, delete_pnp_context):
    context = delete_pnp_context

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, "invalid-token")

    response = client.post(
        "/api/deletePNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "modelName": context["model_name"]
        }
    )

    assert response.status_code == 401
import pytest
from app.auth.auth import COOKIE_NAME, create_token
import uuid
import json

@pytest.mark.asyncio
async def test_integration_create_pnp_investigator_success(client, pnp_case_context):
    context = pnp_case_context

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, context["investigator_token"])

    response = client.post(
        "/api/createPNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "data": {
                "classification": "AI",
                "confidence": 0.91
            }
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Plug-and-play data saved successfully"
    }

    row = await context["conn"].fetchrow(
        """
        SELECT MediaId, ModelResult
        FROM "Cases_DB"."PNPModels"
        WHERE MediaId = $1
        ORDER BY UploadDate DESC
        LIMIT 1
        """,
        context["media_id"]
    )

    assert row is not None
    assert row["mediaid"] == context["media_id"]

    model_result = json.loads(row["modelresult"])

    assert model_result["classification"] == "AI"
    assert model_result["confidence"] == 0.91

@pytest.mark.asyncio
async def test_integration_create_pnp_user_forbidden(client, pnp_case_context):
    context = pnp_case_context

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, context["user_token"])

    response = client.post(
        "/api/createPNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "data": {
                "classification": "AI"
            }
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"

@pytest.mark.asyncio
async def test_integration_create_pnp_unassigned_investigator_forbidden(client, pnp_case_context):
    context = pnp_case_context

    other_token = create_token(
        {
            "id": context["other_investigator_id"],
            "username": context["other_investigator_name"],
            "role": "INVESTIGATOR"
        }
    )

    client.cookies.clear()
    client.cookies.set(
        COOKIE_NAME,
        other_token
    )

    response = client.post(
        "/api/createPNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "data": {
                "classification": "AI"
            }
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"

@pytest.mark.asyncio
async def test_integration_create_pnp_missing_cookie(client, pnp_case_context):
    context = pnp_case_context
    client.cookies.clear()

    response = client.post(
        "/api/createPNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "data": {
                "classification": "AI"
            }
        }
    )

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_integration_create_pnp_invalid_token(client, pnp_case_context):
    context = pnp_case_context

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, "invalid-token")

    response = client.post(
        "/api/createPNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "data": {
                "classification": "AI"
            }
        }
    )

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_integration_create_pnp_media_not_in_case(client, pnp_case_context):
    context = pnp_case_context

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, context["investigator_token"])

    response = client.post(
        "/api/createPNP",
        json={
            "mediaId": str(uuid.uuid4()),
            "caseId": str(context["case_id"]),
            "data": {
                "classification": "AI"
            }
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"

@pytest.mark.asyncio
async def test_integration_create_pnp_admin_success(client, pnp_case_context):
    context = pnp_case_context

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
        "/api/createPNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "data": {
                "classification": "AUTHENTIC",
                "confidence": 0.88
            }
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"

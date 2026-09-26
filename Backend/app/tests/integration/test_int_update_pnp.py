import json
import pytest
from app.auth.auth import COOKIE_NAME, create_token

def updated_pnp_data():
    return {
        "modelName": "TestModel",
        "fileName": "updated.onnx",
        "results": {
            "classification": "AUTHENTIC",
            "confidence": 0.94
        },
        "config": {
            "activation": "softmax"
        },
        "date": "2026-09-26T15:40:00Z"
    }

@pytest.mark.asyncio
async def test_integration_update_pnp_investigator_success(client, update_pnp_context):
    context = update_pnp_context

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, context["investigator_token"])

    response = client.post(
        "/api/updatePNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "data": updated_pnp_data()
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Plug-and-play data updated successfully"
    }

    row = await context["conn"].fetchrow(
        """
        SELECT ModelName, ModelResult
        FROM "Cases_DB"."PNPModels"
        WHERE MediaId = $1
          AND ModelName = $2
        """,
        context["media_id"],
        context["model_name"]
    )

    assert row is not None
    assert row["modelname"] == "TestModel"

    result = json.loads(row["modelresult"])

    assert result["fileName"] == "updated.onnx"
    assert result["results"]["classification"] == "AUTHENTIC"
    assert result["results"]["confidence"] == 0.94
    assert result["config"]["activation"] == "softmax"

@pytest.mark.asyncio
async def test_integration_update_pnp_admin_success(client, update_pnp_context):
    context = update_pnp_context

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
        "/api/updatePNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "data": updated_pnp_data()
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_integration_update_pnp_user_forbidden(client, update_pnp_context):
    context = update_pnp_context

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, context["user_token"])

    response = client.post(
        "/api/updatePNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "data": updated_pnp_data()
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"

@pytest.mark.asyncio
async def test_integration_update_pnp_unassigned_investigator_forbidden(client, update_pnp_context):
    context = update_pnp_context

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
        "/api/updatePNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "data": updated_pnp_data()
        }
    )

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"

@pytest.mark.asyncio
async def test_integration_update_pnp_wrong_model_name(client, update_pnp_context):
    context = update_pnp_context

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, context["investigator_token"])

    data = updated_pnp_data()
    data["modelName"] = "WrongModel"

    response = client.post(
        "/api/updatePNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "data": data
        }
    )

    assert response.status_code == 403

    row = await context["conn"].fetchrow(
        """
        SELECT ModelResult
        FROM "Cases_DB"."PNPModels"
        WHERE MediaId = $1
          AND ModelName = $2
        """,
        context["media_id"],
        context["model_name"]
    )

    result = json.loads(row["modelresult"])

    assert result["fileName"] == "original.onnx"
    assert result["results"]["confidence"] == 0.60

@pytest.mark.asyncio
async def test_integration_update_pnp_missing_model_name(client, update_pnp_context):
    context = update_pnp_context

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, context["investigator_token"])

    data = updated_pnp_data()
    del data["modelName"]

    response = client.post(
        "/api/updatePNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "data": data
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "status": "error",
        "message": "Model name is required"
    }

@pytest.mark.asyncio
async def test_integration_update_pnp_missing_cookie(client, update_pnp_context):
    context = update_pnp_context
    client.cookies.clear()

    response = client.post(
        "/api/updatePNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "data": updated_pnp_data()
        }
    )

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_integration_update_pnp_invalid_token(client, update_pnp_context):
    context = update_pnp_context

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, "invalid-token")

    response = client.post(
        "/api/updatePNP",
        json={
            "mediaId": str(context["media_id"]),
            "caseId": str(context["case_id"]),
            "data": updated_pnp_data()
        }
    )

    assert response.status_code == 401
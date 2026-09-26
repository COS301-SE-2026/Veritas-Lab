import json
import pytest
import asyncpg
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from app.api.routers.cases_router import update_plug_and_play, plug_and_play_request

@pytest.fixture
def mock_verify_jwt(monkeypatch):
    def _mock(payload):
        mock = AsyncMock(return_value=payload)

        monkeypatch.setattr(
            "app.api.routers.cases_router.verify_jwt",
            mock
        )

        return mock

    return _mock

@pytest.fixture
def pnp_request():
    return plug_and_play_request(
        mediaId="11111111-1111-1111-1111-111111111111",
        caseId="22222222-2222-2222-2222-222222222222",
        data={
            "modelName": "TestModel",
            "fileName": "test.onnx",
            "results": {
                "classification": "AI",
                "confidence": 0.91
            },
            "config": {},
            "date": "2026-09-26T15:40:00Z"
        }
    )

@pytest.mark.asyncio
async def test_update_pnp_investigator_success(mock_verify_jwt, pnp_request):
    request = MagicMock()

    connection = AsyncMock()
    connection.fetchrow.return_value = {
        "pnpmodelid": 1,
        "mediaid": pnp_request.mediaId,
        "modelname": "TestModel",
        "modelresult": pnp_request.data,
        "uploaddate": None
    }

    mock_jwt = mock_verify_jwt({
        "username": "Test_Investigator",
        "role": "INVESTIGATOR"
    })

    response = await update_plug_and_play(pnp_request, request, connection)

    assert response == {
        "status": "success",
        "message": "Plug-and-play data updated successfully"
    }

    mock_jwt.assert_awaited_once_with(request, connection)
    connection.fetchrow.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_pnp_admin_success(mock_verify_jwt, pnp_request):
    request = MagicMock()

    connection = AsyncMock()
    connection.fetchrow.return_value = {
        "pnpmodelid": 2
    }

    mock_jwt = mock_verify_jwt({
        "username": "Test_Admin",
        "role": "ADMIN"
    })

    response = await update_plug_and_play(pnp_request, request, connection)

    assert response["status"] == "success"
    assert response["message"] == "Plug-and-play data updated successfully"

    mock_jwt.assert_awaited_once_with(request, connection)
    connection.fetchrow.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_pnp_unauthorized_role(
    mock_verify_jwt,
    pnp_request
):
    request = MagicMock()
    connection = AsyncMock()

    mock_jwt = mock_verify_jwt({
        "username": "Test_User",
        "role": "USER"
    })

    with pytest.raises(HTTPException) as exc:
        await update_plug_and_play(pnp_request, request, connection)

    assert exc.value.status_code == 403
    assert exc.value.detail["status"] == "error"

    mock_jwt.assert_awaited_once_with(request, connection)
    connection.fetchrow.assert_not_awaited()

@pytest.mark.asyncio
async def test_update_pnp_missing_model_name(mock_verify_jwt):
    request = MagicMock()
    connection = AsyncMock()

    mock_jwt = mock_verify_jwt({
        "username": "Test_Investigator",
        "role": "INVESTIGATOR"
    })

    request_body = plug_and_play_request(
        mediaId="11111111-1111-1111-1111-111111111111",
        caseId="22222222-2222-2222-2222-222222222222",
        data={
            "fileName": "test.onnx",
            "results": {
                "classification": "AI",
                "confidence": 0.91
            },
            "config": {},
            "date": "2026-09-26T15:40:00Z"
        }
    )

    with pytest.raises(HTTPException) as exc:
        await update_plug_and_play(request_body, request, connection)

    assert exc.value.status_code == 400
    assert exc.value.detail == {
        "status": "error",
        "message": "Model name is required"
    }

    mock_jwt.assert_awaited_once_with(request, connection)
    connection.fetchrow.assert_not_awaited()

@pytest.mark.asyncio
async def test_update_pnp_not_found_or_not_assigned(mock_verify_jwt, pnp_request):
    request = MagicMock()

    connection = AsyncMock()
    connection.fetchrow.return_value = None

    mock_jwt = mock_verify_jwt({
        "username": "Test_Investigator",
        "role": "INVESTIGATOR"
    })

    with pytest.raises(HTTPException) as exc:
        await update_plug_and_play(pnp_request, request, connection)

    assert exc.value.status_code == 403
    assert exc.value.detail["status"] == "error"

    mock_jwt.assert_awaited_once_with(request, connection)
    connection.fetchrow.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_pnp_database_error(mock_verify_jwt, pnp_request):
    request = MagicMock()

    connection = AsyncMock()
    connection.fetchrow.side_effect = asyncpg.PostgresError("Database failure")

    mock_jwt = mock_verify_jwt({
        "username": "Test_Admin",
        "role": "ADMIN"
    })

    with pytest.raises(HTTPException) as exc:
        await update_plug_and_play(pnp_request, request, connection)

    assert exc.value.status_code == 500
    assert exc.value.detail["status"] == "error"

    mock_jwt.assert_awaited_once_with(request, connection)
    connection.fetchrow.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_pnp_passes_correct_values(mock_verify_jwt, pnp_request):
    request = MagicMock()

    connection = AsyncMock()
    connection.fetchrow.return_value = {
        "pnpmodelid": 1
    }

    mock_verify_jwt({
        "username": "Test_Investigator",
        "role": "INVESTIGATOR"
    })

    await update_plug_and_play(pnp_request, request, connection)

    args = connection.fetchrow.await_args.args

    assert json.loads(args[1]) == pnp_request.data
    assert args[2] == pnp_request.mediaId
    assert args[3] == "TestModel"
    assert args[4] == pnp_request.caseId
    assert args[5] == "Test_Investigator"
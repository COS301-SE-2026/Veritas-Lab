import pytest
import asyncpg
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from app.api.routers.cases_router import create_plug_and_play, plug_and_play_request

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
            "classification": "AI",
            "confidence": 0.91
        }
    )

@pytest.mark.asyncio
async def test_create_pnp_success(mock_verify_jwt, pnp_request):
    request = MagicMock()

    connection = AsyncMock()
    connection.fetchrow.return_value = {
        "pnpmodelid": 1,
        "mediaid": pnp_request.mediaId,
        "modelresult": pnp_request.data,
        "uploaddate": None
    }

    mock_jwt = mock_verify_jwt({
        "username": "Test_Investigator",
        "role": "INVESTIGATOR"
    })

    response = await create_plug_and_play(pnp_request, request, connection)

    assert response == {
        "status": "success",
        "message": "Plug-and-play data saved successfully"
    }

    mock_jwt.assert_awaited_once_with(request, connection)
    connection.fetchrow.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_pnp_admin_success(mock_verify_jwt, pnp_request):
    request = MagicMock()
    connection = AsyncMock()
    connection.fetchrow.return_value = {
        "pnpmodelid": 2,
        "mediaid": pnp_request.mediaId,
        "modelresult": pnp_request.data,
        "uploaddate": None
    }

    mock_jwt = mock_verify_jwt({
        "username": "Test_Admin",
        "role": "ADMIN"
    })

    response = await create_plug_and_play(pnp_request, request, connection)

    assert response["status"] == "success"
    assert response["message"] == "Plug-and-play data saved successfully"
    
    mock_jwt.assert_awaited_once_with(request, connection)
    connection.fetchrow.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_pnp_unauthorized_role(mock_verify_jwt, pnp_request):
    request = MagicMock()
    connection = AsyncMock()

    mock_jwt = mock_verify_jwt({
        "username": "Test_User",
        "role": "USER"
    })

    with pytest.raises(HTTPException) as exc:
        await create_plug_and_play(
            pnp_request,
            request,
            connection
        )

    assert exc.value.status_code == 403
    assert exc.value.detail["status"] == "error"

    mock_jwt.assert_awaited_once_with(request, connection)

    connection.fetchrow.assert_not_awaited()

@pytest.mark.asyncio
async def test_create_pnp_not_assigned_to_case(mock_verify_jwt, pnp_request):
    request = MagicMock()

    connection = AsyncMock()
    connection.fetchrow.return_value = None

    mock_jwt = mock_verify_jwt({
        "username": "Test_Investigator",
        "role": "INVESTIGATOR"
    })

    with pytest.raises(HTTPException) as exc:
        await create_plug_and_play(
            pnp_request,
            request,
            connection
        )

    assert exc.value.status_code == 403
    assert exc.value.detail["status"] == "error"

    mock_jwt.assert_awaited_once_with(request, connection)

    connection.fetchrow.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_pnp_database_error(mock_verify_jwt, pnp_request):
    request = MagicMock()

    connection = AsyncMock()
    connection.fetchrow.side_effect = asyncpg.PostgresError("Database failure")

    mock_jwt = mock_verify_jwt({
        "username": "Test_Admin",
        "role": "ADMIN"
    })

    with pytest.raises(HTTPException) as exc:
        await create_plug_and_play(
            pnp_request,
            request,
            connection
        )

    assert exc.value.status_code == 500
    assert exc.value.detail["status"] == "error"

    mock_jwt.assert_awaited_once_with(
        request,
        connection
    )

    connection.fetchrow.assert_awaited_once()
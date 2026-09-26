import pytest
import asyncpg
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from app.api.routers.cases_router import create_plug_and_play
from app.api.routers.cases_router import plug_and_play_request

@pytest.mark.asyncio
async def test_create_pnp_success(monkeypatch):
    request = MagicMock()

    connection = AsyncMock()
    connection.fetchrow.return_value = {
        "pnpmodelid": 1,
        "mediaid": "11111111-1111-1111-1111-111111111111",
        "modelresult": {
            "classification": "AI",
            "confidence": 0.91
        },
        "uploaddate": None
    }

    monkeypatch.setattr(
        "app.api.routers.cases_router.verify_jwt",
        lambda request: {
            "username": "Test_Investigator",
            "role": "INVESTIGATOR"
        }
    )

    pnp_request = plug_and_play_request(
        mediaId="11111111-1111-1111-1111-111111111111",
        caseId="22222222-2222-2222-2222-222222222222",
        data={
            "classification": "AI",
            "confidence": 0.91
        }
    )

    response = await create_plug_and_play(pnp_request, request, connection)

    assert response == {
        "status": "success",
        "message": "Plug-and-play data saved successfully"
    }

    connection.fetchrow.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_pnp_unauthorized_role(monkeypatch):
    request = MagicMock()
    connection = AsyncMock()

    monkeypatch.setattr(
        "app.api.routers.cases_router.verify_jwt",
        lambda request: {
            "username": "Test_User",
            "role": "USER"
        }
    )

    pnp_request = plug_and_play_request(
        mediaId="11111111-1111-1111-1111-111111111111",
        caseId="22222222-2222-2222-2222-222222222222",
        data={
            "classification": "AI",
            "confidence": 0.91
        }
    )

    with pytest.raises(HTTPException) as exc:
        await create_plug_and_play(pnp_request, request, connection)

    assert exc.value.status_code == 403
    assert exc.value.detail["status"] == "error"

    connection.fetchrow.assert_not_awaited()

@pytest.mark.asyncio
async def test_create_pnp_not_assigned_to_case(monkeypatch):
    request = MagicMock()
    connection = AsyncMock()
    connection.fetchrow.return_value = None

    monkeypatch.setattr(
        "app.api.routers.cases_router.verify_jwt",
        lambda request: {
            "username": "Test_Investigator",
            "role": "INVESTIGATOR"
        }
    )

    pnp_request = plug_and_play_request(
        mediaId="11111111-1111-1111-1111-111111111111",
        caseId="22222222-2222-2222-2222-222222222222",
        data={
            "classification": "AI",
            "confidence": 0.91
        }
    )

    with pytest.raises(HTTPException) as exc:
        await create_plug_and_play(pnp_request, request, connection)

    assert exc.value.status_code == 403
    assert exc.value.detail["status"] == "error"

    connection.fetchrow.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_pnp_database_error(monkeypatch):
    request = MagicMock()
    connection = AsyncMock()
    connection.fetchrow.side_effect = asyncpg.PostgresError(
        "Database failure"
    )

    monkeypatch.setattr(
        "app.api.routers.cases_router.verify_jwt",
        lambda request: {
            "username": "Test_Admin",
            "role": "ADMIN"
        }
    )

    pnp_request = plug_and_play_request(
        mediaId="11111111-1111-1111-1111-111111111111",
        caseId="22222222-2222-2222-2222-222222222222",
        data={
            "classification": "AUTHENTIC",
            "confidence": 0.88
        }
    )

    with pytest.raises(HTTPException) as exc:
        await create_plug_and_play(pnp_request, request, connection)

    assert exc.value.status_code == 500
    assert exc.value.detail["status"] == "error"

    connection.fetchrow.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_pnp_admin_success(monkeypatch):
    request = MagicMock()
    connection = AsyncMock()
    connection.fetchrow.return_value = {
        "pnpmodelid": 2
    }

    monkeypatch.setattr(
        "app.api.routers.cases_router.verify_jwt",
        lambda request: {
            "username": "Test_Admin",
            "role": "ADMIN"
        }
    )

    pnp_request = plug_and_play_request(
        mediaId="11111111-1111-1111-1111-111111111111",
        caseId="22222222-2222-2222-2222-222222222222",
        data={
            "classification": "AI"
        }
    )

    response = await create_plug_and_play(pnp_request, request, connection)

    assert response["status"] == "success"
    connection.fetchrow.assert_awaited_once()
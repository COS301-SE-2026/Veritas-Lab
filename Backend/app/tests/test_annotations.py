from uuid import UUID
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
import asyncpg


from app.api.main import app
import app.api.routers.cases_router as cases_router


@pytest.fixture
def valid_payload():
    return {
        "caseId": "case_123",
        "evidenceId": "ev_456",
        "reportId": "19dccebd-302b-412a-b77e-3167f79837d1",
        "annotations": [
            {"tag": "highlight", "cord": "15-35"},
            {"tag": "comment", "cord": "35-23"}
        ]
    }

@pytest.mark.asyncio
async def test_save_annotations_success(valid_payload):
    with patch.object(cases_router, "verify_jwt_", return_value={"role": "admin"}), \
         patch.object(cases_router, "verify_not_user", return_value=True), \
         patch.object(cases_router, "transform_to_uuid", return_value=UUID("19dccebd-302b-412a-b77e-3167f79837d1")), \
         patch.object(cases_router, "_save_annotations", new_callable=AsyncMock) as mock_save:

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="https://test"
        ) as ac:
            response = await ac.post("/api/saveAnnotations", json=valid_payload)

        assert response.status_code == 200
        assert response.json() == {"status": "success"}
        mock_save.assert_called_once()

@pytest.mark.asyncio
async def test_save_annotations_unauthorized(valid_payload):
    with patch.object(cases_router, "verify_jwt_", return_value={"role": "unauthorized_role"}), \
         patch.object(cases_router, "verify_not_user", side_effect=HTTPException(status_code=403, detail="Forbidden")):

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="https://test"
        ) as ac:
            response = await ac.post("/api/saveAnnotations", json=valid_payload)

        assert response.status_code == 403

@pytest.mark.asyncio
async def test_save_annotations_invalid_payload():
    invalid_payload = {
        "caseId": "case_123"
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="https://test"
    ) as ac:
        response = await ac.post("/api/saveAnnotations", json=invalid_payload)

    assert response.status_code == 422

@pytest.mark.asyncio
async def test_save_annotations_db_error(valid_payload):
    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = asyncpg.PostgresError("DB execution failed")

    with patch.object(cases_router, "verify_jwt_", return_value={"role": "admin"}), \
         patch.object(cases_router, "verify_not_user", return_value=True), \
         patch.object(cases_router, "transform_to_uuid", return_value=UUID("19dccebd-302b-412a-b77e-3167f79837d1")), \
         patch.object(cases_router, "get_connection", return_value=mock_conn):

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="https://test"
        ) as ac:
            response = await ac.post("/api/saveAnnotations", json=valid_payload)

        assert response.status_code == 500
        assert response.json() == {
            "detail": {
                "status": "error",
                "message": "Database error"
            }
        }
        mock_conn.close.assert_called_once()
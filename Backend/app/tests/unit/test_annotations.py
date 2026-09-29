from uuid import UUID
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
import asyncpg


from app.api.main import app
import app.api.routers.cases_router as cases_router
from app.core.database import get_connection 
from app.tests.unit.database_override import unit_get_connection


@pytest.fixture(autouse=True)
def override_database_dependency():
    app.dependency_overrides[get_connection] = unit_get_connection
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_connection, None)


@pytest.fixture
def valid_payload():
    return {
        "caseId": "19dccebd-302b-412a-b77e-3167f79837d1",
        "mediaId": "19dccebd-302b-412a-b77e-3167f79837d1",
        "annotations": [
            {"tag": "highlight", "cord": "15-35"},
            {"tag": "comment", "cord": "35-23"}
        ]
    }

@pytest.mark.asyncio
async def test_save_annotations_success(valid_payload):
    with patch.object(cases_router, "verify_jwt", return_value={
             "role": "ADMIN",
             "username": "assigned_investigator",
             "sub": str(UUID("19dccebd-302b-412a-b77e-3167f79837d1")),
         }), \
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
    with patch.object(cases_router, "verify_jwt", return_value={"role": "unauthorized_role"}), \
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
async def test_save_annotations_requires_case_assignment():
    connection = AsyncMock()
    connection.transaction = MagicMock()
    connection.fetchrow.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await cases_router._save_annotations(
            connection=connection,
            case_id=UUID("19dccebd-302b-412a-b77e-3167f79837d1"),
            media_id=UUID("29dccebd-302b-412a-b77e-3167f79837d1"),
            annotations="[]",
            user_name="unassigned_investigator",
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["message"] == cases_router.USER_UNAUTHORIZED


import json
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
        "caseBoard": {
            "nodes": [
                {
                    "id": "1", 
                    "type": "note", 
                    "text": "Suspect vehicle"
                }
            ],
            "edges": []
        }
    }

@pytest.fixture
def expected_response_payload():
    return {
        "status": "success",
        "caseId": "19dccebd-302b-412a-b77e-3167f79837d1",
        "caseBoard": {
            "nodes": [
                {
                    "id": "1", 
                    "type": "note", 
                    "text": "Suspect vehicle"
                }
            ],
            "edges": []
        }
    }

@pytest.mark.asyncio
async def test_save_case_board_success(valid_payload):
    with patch.object(cases_router, "verify_jwt", return_value={
             "role": "ADMIN",
             "username": "assigned_investigator",
             "sub": str(UUID("19dccebd-302b-412a-b77e-3167f79837d1")),
         }), \
         patch.object(cases_router, "verify_not_user", return_value=True), \
         patch.object(cases_router, "transform_to_uuid", return_value=UUID("19dccebd-302b-412a-b77e-3167f79837d1")), \
         patch.object(cases_router, "save_case_board_helper", new_callable=AsyncMock) as mock_save:

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="https://test"
        ) as ac:
            response = await ac.post("/api/saveCaseBoard", json=valid_payload)

        assert response.status_code == 200
        assert response.json() == {"status": "success"}
        mock_save.assert_called_once()

@pytest.mark.asyncio
async def test_save_case_board_unauthorized(valid_payload):
    with patch.object(cases_router, "verify_jwt", return_value={"role": "unauthorized_role"}), \
         patch.object(cases_router, "verify_not_user", side_effect=HTTPException(status_code=403, detail="Forbidden")):

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="https://test"
        ) as ac:
            response = await ac.post("/api/saveCaseBoard", json=valid_payload)

        assert response.status_code == 403

@pytest.mark.asyncio
async def test_save_case_board_invalid_payload():
    invalid_payload = {
        "caseId": "case_123"
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="https://test"
    ) as ac:
        response = await ac.post("/api/saveCaseBoard", json=invalid_payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_save_case_board_requires_case_assignment():
    connection = AsyncMock()
    connection.transaction = MagicMock()
    connection.fetchrow.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await cases_router.save_case_board_helper(
            connection=connection,
            case_id=UUID("19dccebd-302b-412a-b77e-3167f79837d1"),
            case_board="{}",
            user_name="unassigned_investigator",
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["message"] == cases_router.USER_UNAUTHORIZED

@pytest.mark.asyncio
async def test_get_case_board_success(expected_response_payload):
    case_id_str = expected_response_payload["caseId"]
    db_case_board_json = json.dumps(expected_response_payload["caseBoard"])
    
    with patch.object(cases_router, "verify_jwt", return_value={"role": "INVESTIGATOR"}), \
         patch.object(cases_router, "verify_not_user", return_value=True):
        
        mock_connection = AsyncMock()
        mock_connection.fetchrow.side_effect = [
            {"casestate": "CLOSED"},
            {"caseboard": db_case_board_json}
        ]
        
        async def override_get_connection():
            yield mock_connection
            
        app.dependency_overrides[get_connection] = override_get_connection

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="https://test"
            ) as ac:
                response = await ac.get(f"/api/getCaseBoard/{case_id_str}")

            assert response.status_code == 200
            assert response.json() == expected_response_payload
        finally:
            app.dependency_overrides[get_connection] = unit_get_connection

@pytest.mark.asyncio
async def test_get_case_board_invalid_uuid():
    with patch.object(cases_router, "verify_jwt", return_value={"role": "ADMIN"}), \
         patch.object(cases_router, "verify_not_user", return_value=True), \
         patch.object(cases_router, "transform_to_uuid", side_effect=HTTPException(status_code=400)):
         
        mock_connection = AsyncMock()
        
        async def override_get_connection():
            yield mock_connection
            
        app.dependency_overrides[get_connection] = override_get_connection

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="https://test"
            ) as ac:
                response = await ac.get("/api/getCaseBoard/invalid-uuid-string")

            assert response.status_code == 400
        finally:
            app.dependency_overrides[get_connection] = unit_get_connection

@pytest.mark.asyncio
async def test_get_case_board_not_found():
    valid_uuid = "19dccebd-302b-412a-b77e-3167f79837d1"
    
    with patch.object(cases_router, "verify_jwt", return_value={"role": "INVESTIGATOR"}), \
         patch.object(cases_router, "verify_not_user", return_value=True):
         
        mock_connection = AsyncMock()
        mock_connection.fetchrow.return_value = None
        
        async def override_get_connection():
            yield mock_connection
            
        app.dependency_overrides[get_connection] = override_get_connection

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="https://test"
            ) as ac:
                response = await ac.get(f"/api/getCaseBoard/{valid_uuid}")

            assert response.status_code == 404
        finally:
            app.dependency_overrides[get_connection] = unit_get_connection

@pytest.mark.asyncio
async def test_get_case_board_open_case_forbidden():
    valid_uuid = "19dccebd-302b-412a-b77e-3167f79837d1"
    
    with patch.object(cases_router, "verify_jwt", return_value={"role": "INVESTIGATOR"}), \
         patch.object(cases_router, "verify_not_user", return_value=True):
         
        mock_connection = AsyncMock()
        mock_connection.fetchrow.return_value = {"casestate": "OPEN"}
        
        async def override_get_connection():
            yield mock_connection
            
        app.dependency_overrides[get_connection] = override_get_connection

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="https://test"
            ) as ac:
                response = await ac.get(f"/api/getCaseBoard/{valid_uuid}")

            assert response.status_code == 403
        finally:
            app.dependency_overrides[get_connection] = unit_get_connection
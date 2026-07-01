import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone

from app.api.main import app
from app.core.cases import Case
import app.api.routers.cases_router as cases_router

import uuid
from uuid import uuid4

client = TestClient(app)

def test_case_creation_with_valid_data():
    client.cookies.clear()
    case = Case(CaseCreator="James Bond", CaseName="Flood in Durban")
    
    assert case.CaseCreator == "James Bond"
    assert case.CaseName == "Flood in Durban"
    assert case.CaseId is None
    assert case.CaseCreationDate is None
    assert case.CaseClosed is False

def test_case_creation_requires_creator():
    client.cookies.clear()
    with pytest.raises(ValueError, match="CaseCreator is required"):
        Case(CaseName="Test Case")

def test_case_creation_requires_case_name():
    client.cookies.clear()
    with pytest.raises(ValueError, match="CaseName is required"):
        Case(CaseCreator="alice_dev")

def test_case_creation_rejects_blank_creator():
    client.cookies.clear()
    with pytest.raises(ValueError, match="CaseCreator is required"):
        Case(CaseCreator="   ", CaseName="Test Case")

def test_case_creation_rejects_blank_case_name():
    client.cookies.clear()
    with pytest.raises(ValueError, match="CaseName is required"):
        Case(CaseCreator="alice_dev", CaseName="   ")

def test_name_is_too_long():
    client.cookies.clear()
    with pytest.raises(ValueError, match="Name is too long"):
        Case(
            CaseName="Test Case",
            CaseCreator="A" * 101
        )

def test_name_at_100_characters():
    client.cookies.clear()
    creator_name_100 = "A" * 100

    case = Case(
        CaseName="Test Case",
        CaseCreator=creator_name_100
    )

    assert len(case.CaseCreator) == 100
    assert case.CaseCreator == creator_name_100

def test_case_name_at_99_characters():
    client.cookies.clear()
    case_name_99 = "A" * 99
    case = Case(CaseCreator="alice_dev", CaseName=case_name_99)
    
    assert len(case.CaseName) == 99
    assert case.CaseName == case_name_99

def test_case_name_at_254_characters():
    client.cookies.clear()
    case_name_254 = "A" * 254
    case = Case(CaseCreator="alice_dev", CaseName=case_name_254)
    
    assert len(case.CaseName) == 254
    assert case.CaseName == case_name_254

def test_case_name_at_255_characters():
    client.cookies.clear()
    case_name_255 = "A" * 255
    case = Case(CaseCreator="alice_dev", CaseName=case_name_255)
    
    assert len(case.CaseName) == 255
    assert case.CaseName == case_name_255

def test_case_name_at_256_characters():
    client.cookies.clear()
    case_name_256 = "A" * 256
    
    with pytest.raises(ValueError, match="CaseName must be 255 characters or less"):
        Case(CaseCreator="alice_dev", CaseName=case_name_256)

def test_case_stores_description():
    client.cookies.clear()
    case = Case(
        CaseCreator="alice_dev",
        CaseName="Test Case",
        CaseDescription="This is a test description"
    )

    assert case.CaseDescription == "This is a test description"

def test_case_stores_reviews():
    client.cookies.clear()
    reviews = {
        "reviewer": "admin",
        "status": "pending"
    }

    case = Case(
        CaseCreator="alice_dev",
        CaseName="Test Case",
        CaseReviews=reviews
    )

    assert case.CaseReviews == reviews

def test_case_to_json_before_create():
    client.cookies.clear()
    case = Case(
        CaseCreator="alice_dev",
        CaseName="Test Case",
        CaseDescription="This is a test description",
        CaseReviews={"status": "pending"}
    )

    result = case.toJSON()

    assert result == {
        "caseId": None,
        "caseName": "Test Case",
        "caseCreator": "alice_dev",
        "caseReviews": {"status": "pending"},
        "caseDescription": "This is a test description",
        "caseClosed": False,
        "caseCreationDate": None
    }

def test_case_to_json_after_create_values_set():
    client.cookies.clear()
    case = Case(
        CaseCreator="alice_dev",
        CaseName="Test Case",
        CaseDescription="This is a test description",
        CaseReviews={"reviewer": "admin", "status": "approved"}
    )

    case.CaseId = "12345678-abcd-ef01-2345-6789abcdef01"
    case.CaseClosed = True
    case.CaseCreationDate = datetime(2026, 5, 20, 19, 43, 2, tzinfo=timezone.utc)

    result = case.toJSON()

    assert result == {
        "caseId": "12345678-abcd-ef01-2345-6789abcdef01",
        "caseName": "Test Case",
        "caseCreator": "alice_dev",
        "caseReviews": {"reviewer": "admin", "status": "approved"},
        "caseDescription": "This is a test description",
        "caseClosed": True,
        "caseCreationDate": "2026-05-20T19:43:02+00:00"
    }

def test_case_to_json_with_no_description_or_reviews():
    client.cookies.clear()
    case = Case(
        CaseCreator="alice_dev",
        CaseName="Test Case"
    )

    assert case.toJSON() == {
        "caseId": None,
        "caseName": "Test Case",
        "caseCreator": "alice_dev",
        "caseReviews": None,
        "caseDescription": None,
        "caseClosed": False,
        "caseCreationDate": None
    }

@pytest.mark.asyncio
@patch("asyncpg.connect")
async def test_create_case_with_mock(mock_connect):
    client.cookies.clear()
    case = Case(
        CaseCreator="alice_dev",
        CaseName="Test Case",
        CaseDescription="Mock description"
    )

    fake_db_uuid = "12345678-abcd-ef01-2345-6789abcdef01"
    fake_creation_date = "2026-05-20T16:00:00Z"

    mock_connection = AsyncMock()
    mock_connect.return_value = mock_connection
    mock_connection.close = AsyncMock(return_value=None)

    mock_connection.fetchrow = AsyncMock(return_value={
        "caseid": fake_db_uuid,
        "casecreationdate": fake_creation_date
    })

    case_id = await case.create()

    assert case_id == fake_db_uuid
    assert isinstance(case_id, str)

    assert str(case.CaseId) == fake_db_uuid
    assert case.CaseCreationDate == fake_creation_date

    called_args = mock_connection.fetchrow.call_args[0]

    params = called_args[1:]

    assert params == (
        case.CaseCreator,
        case.CaseName,
        None,
        case.CaseDescription,
        case.CaseClosed
    )

    mock_connect.assert_called_once()
    mock_connection.fetchrow.assert_called_once()
    mock_connection.close.assert_called_once()

@pytest.mark.asyncio
@patch("asyncpg.connect")
async def test_create_case_cannot_be_called_twice(mock_connect):
    client.cookies.clear()
    case = Case(CaseCreator="alice_dev", CaseName="Test Case")
    case.CaseId = "12345678-abcd-ef01-2345-6789abcdef01"

    with pytest.raises(ValueError, match="This case already exists"):
        await case.create()

    mock_connect.assert_not_called()

def test_get_cases_missing_jwt(monkeypatch):
    client.cookies.clear()
    def mock_verifyJWT(request):
        raise ValueError("Missing Authorization header")

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post("/api/getCases", json={})

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Missing Authorization header"
    }

def test_get_cases_invalid_jwt(monkeypatch):
    client.cookies.clear()
    def mock_verifyJWT(request):
        raise ValueError("Invalid token")

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/getCases",
        json={}
    )

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Invalid token"
    }

def test_get_cases_admin_returns_cases(monkeypatch):
    client.cookies.clear()
    def mock_verifyJWT(request):
        return {
            "sub": "mock-admin-id",
            "username": "admin_user",
            "role": "ADMIN"
        }

    fake_rows = [
        {
            "caseid": "12345678-abcd-ef01-2345-6789abcdef01",
            "casecreator": "admin_user",
            "casename": "Flood in Durban",
            "casereviews": None,
            "casedescription": "Flood investigation case",
            "caseclosed": False,
            "casecreationdate": datetime(2026, 5, 20, 19, 43, 2, tzinfo=timezone.utc)
        },
        {
            "caseid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "casecreator": "investigator_user",
            "casename": "Fake Evidence Case",
            "casereviews": {"status": "pending"},
            "casedescription": "Media verification case",
            "caseclosed": False,
            "casecreationdate": datetime(2026, 5, 21, 10, 30, 0, tzinfo=timezone.utc)
        }
    ]

    mock_connection = AsyncMock()
    mock_connection.fetch = AsyncMock(return_value=fake_rows)
    mock_connection.close = AsyncMock(return_value=None)

    mock_connect = AsyncMock(return_value=mock_connection)

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.asyncpg, "connect", mock_connect)

    response = client.post(
        "/api/getCases",
        json={}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"
    assert len(data["cases"]) == 2

    assert data["cases"][0] == {
        "caseId": "12345678-abcd-ef01-2345-6789abcdef01",
        "caseName": "Flood in Durban",
        "caseCreator": "admin_user",
        "caseReviews": None,
        "caseDescription": "Flood investigation case",
        "caseClosed": False,
        "caseCreationDate": "2026-05-20T19:43:02+00:00"
    }

    assert data["cases"][1] == {
        "caseId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "caseName": "Fake Evidence Case",
        "caseCreator": "investigator_user",
        "caseReviews": {"status": "pending"},
        "caseDescription": "Media verification case",
        "caseClosed": False,
        "caseCreationDate": "2026-05-21T10:30:00+00:00"
    }

    mock_connect.assert_called_once()
    mock_connection.fetch.assert_called_once()
    mock_connection.close.assert_called_once()

def test_get_cases_investigator_returns_empty_list(monkeypatch):
    client.cookies.clear()
    def mock_verifyJWT(request):
        return {
            "sub": "mock-investigator-id",
            "username": "investigator_user",
            "role": "INVESTIGATOR"
        }

    mock_connection = AsyncMock()
    mock_connection.fetch = AsyncMock(return_value=[])
    mock_connection.close = AsyncMock(return_value=None)

    mock_connect = AsyncMock(return_value=mock_connection)

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.asyncpg, "connect", mock_connect)

    response = client.post(
        "/api/getCases",
        json={}
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "cases": []
    }

    mock_connect.assert_called_once()
    mock_connection.fetch.assert_called_once()
    mock_connection.close.assert_called_once()

def test_get_single_case_missing_jwt(monkeypatch):
    client.cookies.clear()
    def mock_verifyJWT(request):
        raise ValueError("Missing Authorization header")

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post("/api/getSingleCase", json={})

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Missing Authorization header"
    }

def test_get_single_case_invalid_jwt(monkeypatch):
    client.cookies.clear()
    def mock_verifyJWT(request):
        raise ValueError("Invalid token")

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/getSingleCase",
        json={"CaseID": "12345678-abcd-ef01-2345-6789abcdef01"}
    )

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Invalid token"
    }

def test_get_single_case_missing_case_id(monkeypatch):
    client.cookies.clear()
    def mock_verifyJWT(request):
        return {
            "sub": "mock-admin-id",
            "username": "admin_user",
            "role": "ADMIN"
        }

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/getSingleCase",
        json={}
    )

    assert response.status_code == 400
    assert response.json() == {
        "status": "error",
        "message": "CaseID required"
    }

def test_get_single_case_invalid_case_id(monkeypatch):
    client.cookies.clear()
    def mock_verifyJWT(request):
        return {
            "sub": "mock-admin-id",
            "username": "admin_user",
            "role": "ADMIN"
        }

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/getSingleCase",
        json={"CaseID": "not-a-valid-uuid"}
    )

    assert response.status_code == 401
    assert response.json()["status"] == "error"

def test_get_single_case_not_found(monkeypatch):
    client.cookies.clear()
    def mock_verifyJWT(request):
        return {
            "sub": "mock-admin-id",
            "username": "admin_user",
            "role": "ADMIN"
        }

    mock_connection = AsyncMock()
    mock_connection.fetchrow = AsyncMock(return_value=None)
    mock_connection.close = AsyncMock(return_value=None)

    mock_connect = AsyncMock(return_value=mock_connection)

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.asyncpg, "connect", mock_connect)

    response = client.post(
        "/api/getSingleCase",
        json={"CaseID": "12345678-abcd-ef01-2345-6789abcdef01"}
    )

    assert response.status_code == 404
    assert response.json() == {
        "status": "error",
        "message": "Case not found"
    }

    mock_connect.assert_called_once()
    mock_connection.fetchrow.assert_called_once()
    mock_connection.close.assert_called_once()

def test_get_single_case_admin_returns_case(monkeypatch):
    client.cookies.clear()
    def mock_verifyJWT(request):
        return {
            "sub": "mock-admin-id",
            "username": "admin_user",
            "role": "ADMIN"
        }

    mock_minio_client = MagicMock()
    

    fake_case_id = "12345678-abcd-ef01-2345-6789abcdef01"

    fake_row = {
        "caseid": fake_case_id,
        "casecreator": "admin_user",
        "casename": "Flood in Durban",
        "casereviews": {"status": "pending"},
        "casedescription": "Flood investigation case",
        "caseclosed": False,
        "casecreationdate": datetime(2026, 5, 20, 19, 43, 2, tzinfo=timezone.utc)
    }

    mock_connection = AsyncMock()
    mock_connection.fetchrow = AsyncMock(return_value=fake_row)
    mock_connection.fetch = AsyncMock(return_value=[])
    mock_connection.close = AsyncMock(return_value=None)

    mock_connect = AsyncMock(return_value=mock_connection)

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.asyncpg, "connect", mock_connect)

    response = client.post(
        "/api/getSingleCase",
        json={"CaseID": fake_case_id}
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "success",
        "case": {
            "caseId": fake_case_id,
            "caseName": "Flood in Durban",
            "caseCreator": "admin_user",
            "caseReviews": {"status": "pending"},
            "caseDescription": "Flood investigation case",
            "caseClosed": False,
            "caseCreationDate": "2026-05-20T19:43:02+00:00"
        },
        "evidence": []
    }

    fake_media_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    fake_report_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"

    fake_url = f"http://localhost:9000/images/{fake_media_id}.png"
    mock_minio_client.presigned_get_object.return_value = fake_url
    monkeypatch.setattr(cases_router, "Minio", MagicMock(return_value=mock_minio_client))

    fake_evidence_rows = [
    {
        "reportid": fake_report_id,
        "mediaid": fake_media_id,
        "mediatitle": "123",
        "mediabucket": "images",
        "mediaextension": ".png",
        "mediatypeid": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "mediaurl": fake_url,
        "reportartifacts": {"ocr": "captured"},
        "reportfindings": "Flood watermark detected",
        "reportcomments": "Upload approved",
        "reportdatecreation": datetime(2026, 5, 21, 8, 15, 0, tzinfo=timezone.utc)
    }
    ]

    mock_connection = AsyncMock()
    mock_connection.fetchrow = AsyncMock(return_value=fake_row)
    mock_connection.fetch = AsyncMock(return_value=fake_evidence_rows)
    mock_connection.close = AsyncMock(return_value=None)

    mock_connect = AsyncMock(return_value=mock_connection)

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.asyncpg, "connect", mock_connect)

    response = client.post(
        "/api/getSingleCase",
        json={"CaseID": fake_case_id}
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "case": {
            "caseId": fake_case_id,
            "caseName": "Flood in Durban",
            "caseCreator": "admin_user",
            "caseReviews": {"status": "pending"},
            "caseDescription": "Flood investigation case",
            "caseClosed": False,
            "caseCreationDate": "2026-05-20T19:43:02+00:00"
        },
        "evidence": [
            {
                "reportId": fake_report_id,
                "mediaId": fake_media_id,
                "mediaName": "123",
                "mediaBucket": "images",
                "mediaExtension": ".png",
                "mediaTypeId": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "mediaUrl": fake_url,
                "reportArtifacts": {"ocr": "captured"},
                "reportFindings": "Flood watermark detected",
                "reportComments": "Upload approved",
                "reportDateCreation": "2026-05-21T08:15:00+00:00"
            }
        ]
    }

    mock_connect.assert_called_once()
    mock_connection.fetchrow.assert_called_once()
    mock_connection.fetch.assert_called_once()
    mock_connection.close.assert_called_once()

def test_close_case_missing_jwt(monkeypatch):
    client.cookies.clear()
    def mock_verifyJWT(request):
        raise ValueError("Missing Authorization header")
    
    monkeypatch.setattr(cases_router,"verifyJWT", mock_verifyJWT)

    response = client.post("/api/closeCase", json={})

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Missing Authorization header"
    }

def test_close_case_invalid_jwt(monkeypatch):
    client.cookies.clear()
    def mock_verifyJWT(request):
        raise ValueError("Invalid token")

    monkeypatch.setattr(cases_router,"verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/closeCase",
        json={"CaseID": "12345678-abcd-ef01-2345-6789abcdef01"}
    )

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Invalid token"
    }

def test_close_case_user_unauthorized(monkeypatch):
    client.cookies.clear()
    def mock_verifyJWT(request):
        return {
            "sub": "mock-user-id",
            "username": "normal_user",
            "role":"USER"
        }
    
    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/closeCase",
        json={"CaseID": "12345678-abcd-ef01-2345-6789abcdef01"}
    )

    assert response.status_code == 403
    assert response.json() == {
        "status" :"error",
        "message": "User unauthorized"
    }

def test_close_case_invalid_case_id(monkeypatch):
    client.cookies.clear()
    def mock_verifyJWT(request):
        return {
            "sub": "mock-investigator-id",
            "username": "investigator_user",
            "role": "INVESTIGATOR"
        }

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/closeCase",
        json={"CaseID": "not-a-valid-uuid"}
    )

    assert response.status_code == 400
    assert response.json() == {
        "status": "error",
        "message": "Invalid CaseID"
    }

def test_close_case_not_found(monkeypatch):
    client.cookies.clear()
    def mock_verifyJWT(request):
        return {
            "sub": "mock-investigator-id",
            "username": "investigator_user",
            "role": "INVESTIGATOR"
        }
    
    mock_connection = AsyncMock()
    mock_connection.fetchrow = AsyncMock(return_value=None)
    mock_connection.close = AsyncMock(return_value=None)

    mock_connect = AsyncMock(return_value=mock_connection)

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.asyncpg, "connect", mock_connect)

    response = client.post(
        "/api/closeCase",
        json={"CaseID": "12345678-abcd-ef01-2345-6789abcdef01"}
    )

    assert response.status_code == 404
    assert response.json() == {
        "status": "error",
        "message": "Case not found or user unauthorized."
    }

    mock_connect.assert_called_once()
    mock_connection.fetchrow.assert_called_once()
    mock_connection.close.assert_called_once()

def test_close_case_not_case_creator(monkeypatch):
    client.cookies.clear()
    def mock_verifyJWT(request):
        return {
            "sub": "mock-investigator-id",
            "username": "different_user",
            "role": "INVESTIGATOR"
        }


    mock_connection = AsyncMock()
    mock_connection.fetchrow = AsyncMock(return_value=None)
    mock_connection.close = AsyncMock(return_value=None)

    mock_connect = AsyncMock(return_value=mock_connection)

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.asyncpg, "connect", mock_connect)

    response = client.post(
        "/api/closeCase",
        json={"CaseID": "12345678-abcd-ef01-2345-6789abcdef01"}
    )

    assert response.status_code == 404
    assert response.json() == {
        "status": "error",
        "message": "Case not found or user unauthorized."
    }

    mock_connect.assert_called_once()
    mock_connection.fetchrow.assert_called_once()
    mock_connection.close.assert_called_once()

def test_close_case_success_investigator(monkeypatch):
    client.cookies.clear()
    def mock_verifyJWT(request):
        return {
            "sub": "mock-investigator-id",
            "username": "investigator_user",
            "role": "INVESTIGATOR",
        }
    
    fake_case_id = "12345678-abcd-ef01-2345-6789abcdef01"

    fake_row = {
        "caseid": fake_case_id
    }

    mock_connection = AsyncMock()
    mock_connection.fetchrow = AsyncMock(return_value=fake_row)
    mock_connection.close = AsyncMock(return_value=None)

    mock_connect = AsyncMock(return_value=mock_connection)

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.asyncpg, "connect", mock_connect)

    response = client.post(
        "/api/closeCase",
        json={"CaseID": fake_case_id}
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Case closed successfully."
    }

    mock_connect.assert_called_once()
    mock_connection.fetchrow.assert_called_once()
    mock_connection.close.assert_called_once()

    fetchrow_args = mock_connection.fetchrow.call_args[0]

    assert "UPDATE" in fetchrow_args[0]
    assert "caseclosed = TRUE" in fetchrow_args[0]
    assert "casecreator = $2" in fetchrow_args[0]
    assert fetchrow_args[1].hex == "12345678abcdef0123456789abcdef01"
    assert fetchrow_args[2] == "investigator_user"

def test_close_case_success_admin(monkeypatch):
    client.cookies.clear()
    def mock_verifyJWT(request):
        return {
            "sub": "mock-investigator-id",
            "username": "investigator_user",
            "role": "ADMIN",
        }
    
    fake_case_id = "12345678-abcd-ef01-2345-6789abcdef01"

    fake_row = {
        "caseid": fake_case_id
    }

    mock_connection = AsyncMock()
    mock_connection.fetchrow = AsyncMock(return_value=fake_row)
    mock_connection.close = AsyncMock(return_value=None)

    mock_connect = AsyncMock(return_value=mock_connection)

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.asyncpg, "connect", mock_connect)

    response = client.post(
        "/api/closeCase",
        json={"CaseID": fake_case_id}
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Case closed successfully."
    }

    mock_connect.assert_called_once()
    mock_connection.fetchrow.assert_called_once()
    mock_connection.close.assert_called_once()

    fetchrow_args = mock_connection.fetchrow.call_args[0]

    assert "UPDATE" in fetchrow_args[0]
    assert "caseclosed = TRUE" in fetchrow_args[0]
    assert "casecreator = $2" in fetchrow_args[0]
    assert fetchrow_args[1].hex == "12345678abcdef0123456789abcdef01"
    assert fetchrow_args[2] == "investigator_user"

def test_close_case_admin_not_case_creator(monkeypatch):
    client.cookies.clear()
    def mock_verifyJWT(request):
        return {
            "sub": "mock-admin-id",
            "username": "admin_user",
            "role": "ADMIN"
        }
    
    fake_case_id = "12345678-abcd-ef01-2345-6789abcdef01"

    mock_connection = AsyncMock()
    mock_connection.fetchrow = AsyncMock(return_value=None)
    mock_connection.close = AsyncMock(return_value=None)

    mock_connect = AsyncMock(return_value=mock_connection)

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.asyncpg, "connect", mock_connect)

    response = client.post(
        "/api/closeCase",
        json={"CaseID": fake_case_id}
    )

    assert response.status_code == 404
    assert response.json() == {
        "status": "error",
        "message": "Case not found or user unauthorized."
    }

    mock_connect.assert_called_once()
    mock_connection.fetchrow.assert_called_once()
    mock_connection.close.assert_called_once()

    fetchrow_args = mock_connection.fetchrow.call_args[0]

    assert "UPDATE" in fetchrow_args[0]
    assert "caseclosed = TRUE" in fetchrow_args[0]
    assert "casecreator = $2" in fetchrow_args[0]
    assert fetchrow_args[1].hex == "12345678abcdef0123456789abcdef01"
    assert fetchrow_args[2] == "admin_user"

def test_delete_case_success_creator(monkeypatch):
    client.cookies.clear()

    def mock_verifyJWT(request):
        return {
            "sub": "mock-user-id",
            "username": "investigator_user",
            "role": "INVESTIGATOR"
        }
    
    async def mock_deleteCase(case_id: uuid.UUID, username: str, role: str):
        assert isinstance(case_id, uuid.UUID)
        assert str(case_id) == "12345678-abcd-ef01-2345-6789abcdef01"
        assert username == "investigator_user"
        assert role == "INVESTIGATOR"
    
        return {
            "deleted": True,
            "reason": "deleted"
        }
    
    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.Case, "deleteCase", mock_deleteCase)

    response = client.delete(
        "/api/deleteCase",
        json={
            "CaseID": "12345678-abcd-ef01-2345-6789abcdef01"
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Case deleted successfully"
    }

def test_delete_case_success_admin(monkeypatch):
    client.cookies.clear()

    def mock_verifyJWT(request):
        return {
            "sub": "mock-admin-id",
            "username": "admin_user",
            "role": "ADMIN"
        }
    
    async def mock_deleteCase(case_id: uuid.UUID, username: str, role: str):
        assert isinstance(case_id, uuid.UUID)
        assert username == "admin_user"
        assert role == "ADMIN"

        return {
            "deleted": True,
            "reason": "deleted"
        }
    
    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.Case, "deleteCase", mock_deleteCase)

    response = client.delete(
        "/api/deleteCase",
        json={
            "CaseID": "12345678-abcd-ef01-2345-6789abcdef01"
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Case deleted successfully"
    }

def test_delete_case_missing_jwt(monkeypatch):
    client.cookies.clear()

    def mock_verifyJWT(request):
        raise ValueError("Missing token")
    
    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.delete(
        "/api/deleteCase",
        json={
            "CaseID": "12345678-abcd-ef01-2345-6789abcdef01"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Missing token"
    }

def test_delete_case_user_forbidden(monkeypatch):
    client.cookies.clear()

    def mock_verifyJWT(request):
        return {
            "sub": "mock-user-id",
            "username": "normal_user",
            "role": "USER"
        }
    
    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)\
    
    response = client.delete(
        "/api/deleteCase",
        json={
            "CaseID": "12345678-abcd-ef01-2345-6789abcdef01"
        }
    )

    assert response.status_code == 403
    assert response.json() == {
        "status": "error",
        "message": "User unauthorized"
    }

def test_delete_case_missing_case_id(monkeypatch):
    client.cookies.clear()

    def mock_verifyJWT(request):
        return {
            "sub": "mock-investigator-id",
            "username": "investigator_user",
            "role": "INVESTIGATOR"
        }
    
    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.delete(
        "/api/deleteCase",
        json={}
    )

    assert response.status_code == 400
    assert response.json() == {
        "status": "error",
        "message": "CaseID required"
    }

def test_delete_case_invalid_case_id(monkeypatch):
    client.cookies.clear()

    def mock_verifyJWT(request):
        return {
            "sub": "mock-investigator-id",
            "username": "investigator_user",
            "role": "INVESTIGATOR"
        }
    
    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.delete(
        "/api/deleteCase",
        json={
            "CaseID": "not-a-valid-uuid"
        }
    )

    assert response.status_code == 401
    assert response.json()["status"] == "error"

def test_delete_case_not_found(monkeypatch):
    client.cookies.clear()

    def mock_verifyJWT(request):
        return{
            "sub": "mock-investigator-id",
            "username": "investigator_user",
            "role": "INVESTIGATOR"
        }
    
    async def mock_deleteCase(case_id: uuid.UUID, username: str, role: str):
        return {
            "deleted": "False",
            "reason": "not_found"
        }
    
    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.Case, "deleteCase", mock_deleteCase)

    response = client.delete(
        "/api/deleteCase",
        json={
            "CaseID": "12345678-abcd-ef01-2345-6789abcdef01"
        }
    )

    assert response.status_code == 404
    assert response.json() == {
        "status": "error",
        "message": "Case not found"
    }

def test_delete_case_unauthorized_non_creator(monkeypatch):
    client.cookies.clear()

    def mock_verifyJWT(request):
        return {
            "sub": "mock-investigator-id",
            "username": "other_investigator",
            "role": "INVESTIGATOR"
        }
    
    async def mock_deleteCase(case_id: uuid.UUID, username: str, role: str):
        assert username == "other_investigator"
        assert role == "INVESTIGATOR"
        
        return {
            "deleted": False,
            "reason": "unauthorized"
        }
    
    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.Case, "deleteCase", mock_deleteCase)

    response = client.delete(
        "/api/deleteCase",
        json={
            "CaseID": "12345678-abcd-ef01-2345-6789abcdef01"
        }
    )

    assert response.status_code == 403
    assert response.json() == {
        "status": "error",
        "message": "Only the case creator or an admin can delete this case"
    }

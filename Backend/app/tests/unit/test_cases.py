import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone
from fastapi import HTTPException
from uuid import uuid4
import asyncpg

from app.api.main import app
from app.core.cases import Case
import app.api.routers.cases_router as cases_router
from app.auth.auth import NOT_AUTH, INVALID_TOKEN

import uuid
from uuid import uuid4

client = TestClient(app)

def test_case_creation_with_valid_data():
    client.cookies.clear()
    case = Case(case_creator="James Bond", case_name="Flood in Durban")
    
    assert case.case_creator == "James Bond"
    assert case.case_name == "Flood in Durban"
    assert case.case_id is None
    assert case.case_creation_date is None
    assert case.case_closed is False

def test_case_creation_Does_Not_Require_Creator():
    test_case = Case(case_name="Flood in Durban")
    assert test_case.case_creator is None
    assert test_case.case_name == "Flood in Durban"
    assert test_case.case_id is None
    assert test_case.case_creation_date is None
    assert test_case.case_closed is False

def test_case_creation_Does_Not_Require_CaseName():
    test_case = Case(case_creator="Terry")
    assert test_case.case_creator == "Terry"
    assert test_case.case_name is None
    assert test_case.case_id is None
    assert test_case.case_creation_date is None
    assert test_case.case_closed is False

@pytest.mark.asyncio
async def test_case_creation_Rejects_Blank_Creator():
    with pytest.raises(ValueError, match="CaseCreator is required"):
        Case(case_creator="   ", case_name="Test Case")

@pytest.mark.asyncio
async def test_Cas_creation_Rejects_Invalid_UUID():
    with pytest.raises(HTTPException) as exc_info:
        Case(case_id="2")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == {
        "status": "error",
        "message": "'2' is not a valid UUID format"
    }

def test_CaseCreationRejectsBlankCaseName():
    with pytest.raises(ValueError, match="CaseName is required"):
        Case(case_creator="alice_dev", case_name="   ")

def test_name_is_too_long():
    client.cookies.clear()
    with pytest.raises(ValueError, match="Name is too long"):
        Case(case_name="Test Case", case_creator="A" * 101)

def test_name_at_100_characters():
    client.cookies.clear()
    creator_name_100 = "A" * 100

    case = Case(case_name="Test Case", case_creator=creator_name_100)

    assert len(case.case_creator) == 100
    assert case.case_creator == creator_name_100

def test_case_name_at_99_characters():
    client.cookies.clear()
    case_name_99 = "A" * 99
    case = Case(case_creator="alice_dev", case_name=case_name_99)
    
    assert len(case.case_name) == 99
    assert case.case_name == case_name_99

def test_case_name_at_254_characters():
    client.cookies.clear()
    case_name_254 = "A" * 254
    case = Case(case_creator="alice_dev", case_name=case_name_254)
    
    assert len(case.case_name) == 254
    assert case.case_name == case_name_254

def test_case_name_at_255_characters():
    client.cookies.clear()
    case_name_255 = "A" * 255
    case = Case(case_creator="alice_dev", case_name=case_name_255)
    
    assert len(case.case_name) == 255
    assert case.case_name == case_name_255

def test_case_name_at_256_characters():
    client.cookies.clear()
    case_name_256 = "A" * 256
    
    with pytest.raises(ValueError, match="CaseName must be 255 characters or less"):
        Case(case_creator="alice_dev", case_name=case_name_256)

def test_case_stores_description():
    client.cookies.clear()
    case = Case(
        case_creator="alice_dev",
        case_name="Test Case",
        case_description="This is a test description"
    )

    assert case.case_description == "This is a test description"


def test_case_to_json_before_create():
    client.cookies.clear()
    case = Case(
        case_creator="alice_dev",
        case_name="Test Case",
        case_description="This is a test description",
    )

    result = case.to_json()

    assert result == {
        "caseId": None,
        "caseName": "Test Case",
        "caseCreator": "alice_dev",
        "caseDescription": "This is a test description",
        "caseClosed": False,
        "caseCreationDate": None
    }

def test_case_to_json_after_create_values_set():
    client.cookies.clear()
    case = Case(
        case_creator="alice_dev",
        case_name="Test Case",
        case_description="This is a test description",
    )

    case.case_id = "12345678-abcd-ef01-2345-6789abcdef01"
    case.case_closed = True
    case.case_creation_date = datetime(2026, 5, 20, 19, 43, 2, tzinfo=timezone.utc)

    result = case.to_json()

    assert result == {
        "caseId": "12345678-abcd-ef01-2345-6789abcdef01",
        "caseName": "Test Case",
        "caseCreator": "alice_dev",
        "caseDescription": "This is a test description",
        "caseClosed": True,
        "caseCreationDate": "2026-05-20T19:43:02+00:00"
    }

def test_case_to_json_with_no_description_or_reviews():
    client.cookies.clear()
    case = Case(
        case_creator="alice_dev",
        case_name="Test Case"
    )

    assert case.to_json() == {
        "caseId": None,
        "caseName": "Test Case",
        "caseCreator": "alice_dev",
        "caseDescription": None,
        "caseClosed": False,
        "caseCreationDate": None
    }

@pytest.mark.asyncio
@patch("asyncpg.connect")
async def test_create_case_with_mock(mock_connect):
    client.cookies.clear()
    case = Case(
        case_creator="alice_dev",
        case_name="Test Case",
        case_description="Mock description"
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

    assert str(case.case_id) == fake_db_uuid
    assert case.case_creation_date == fake_creation_date

    called_args = mock_connection.fetchrow.call_args[0]

    params = called_args[1:]

    assert params == (
        case.case_creator,
        case.case_name,
        case.case_description,
        case.case_closed
    )

    mock_connect.assert_called_once()
    mock_connection.fetchrow.assert_called_once()
    mock_connection.close.assert_called_once()

@pytest.mark.asyncio
@patch("asyncpg.connect")
async def test_create_case_cannot_be_called_twice(mock_connect):
    client.cookies.clear()
    case = Case(case_creator="alice_dev", case_name="Test Case")
    case.case_id = "12345678-abcd-ef01-2345-6789abcdef01"

    with pytest.raises(HTTPException) as exc_info:
        await case.create()

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == {
        "status": "error",
        "message": "This case already exists"
    }

def test_get_cases_missing_jwt(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt(request):
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error",
                "message": "Missing Authorization header"
            }
        )

    monkeypatch.setattr(
        cases_router,
        "verify_jwt",
        mock_verify_jwt
    )

    response = client.post("/api/getCases", json={})

    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Missing Authorization header"
        }
    }

def test_get_cases_invalid_jwt(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt(request):
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error",
                "message": "Invalid token"
            }
        )

    monkeypatch.setattr(
        cases_router,
        "verify_jwt",
        mock_verify_jwt
    )

    response = client.post(
        "/api/getCases",
        json={}
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Invalid token"
        }
    }

def test_get_cases_admin_returns_cases(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt(request):
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
            "casedescription": "Flood investigation case",
            "caseclosed": False,
            "casecreationdate": datetime(2026, 5, 20, 19, 43, 2, tzinfo=timezone.utc)
        },
        {
            "caseid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "casecreator": "investigator_user",
            "casename": "Fake Evidence Case",
            "casedescription": "Media verification case",
            "caseclosed": False,
            "casecreationdate": datetime(2026, 5, 21, 10, 30, 0, tzinfo=timezone.utc)
        }
    ]

    mock_connection = AsyncMock()
    mock_connection.fetch = AsyncMock(return_value=fake_rows)
    mock_connection.close = AsyncMock(return_value=None)

    mock_connect = AsyncMock(return_value=mock_connection)

    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )
    monkeypatch.setattr(
        cases_router.asyncpg, 
        "connect", 
        mock_connect
    )

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
        "caseDescription": "Flood investigation case",
        "caseClosed": False,
        "caseCreationDate": "2026-05-20T19:43:02+00:00"
    }

    assert data["cases"][1] == {
        "caseId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "caseName": "Fake Evidence Case",
        "caseCreator": "investigator_user",
        "caseDescription": "Media verification case",
        "caseClosed": False,
        "caseCreationDate": "2026-05-21T10:30:00+00:00"
    }

    mock_connect.assert_called_once()
    mock_connection.fetch.assert_called_once()
    mock_connection.close.assert_called_once()

def test_get_cases_investigator_returns_empty_list(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt(request):
        return {
            "sub": "mock-investigator-id",
            "username": "investigator_user",
            "role": "INVESTIGATOR"
        }

    mock_connection = AsyncMock()
    mock_connection.fetch = AsyncMock(return_value=[])
    mock_connection.close = AsyncMock(return_value=None)

    mock_connect = AsyncMock(return_value=mock_connection)

    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )
    monkeypatch.setattr(
        cases_router.asyncpg, 
        "connect", 
        mock_connect
    )

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
    def mock_verify_jwt_(request):
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error",
                "message": "Missing Authorization header"
            }
        )

    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt_
    )

    response = client.post("/api/getSingleCase", json={})

    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Missing Authorization header"
        }
    }

def test_get_single_case_invalid_jwt(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt_(request):
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error",
                "message": "Invalid token"
            }
        )

    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt_
    )

    response = client.post(
        "/api/getSingleCase",
        json={"CaseID": "12345678-abcd-ef01-2345-6789abcdef01"}
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Invalid token"
        }
    }

def test_get_single_case_missing_case_id(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt_(request):
        return {
            "sub": "mock-admin-id",
            "username": "admin_user",
            "role": "ADMIN"
        }

    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt_
    )

    response = client.post(
        "/api/getSingleCase",
        json={}
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "CaseID required"
        }
    }

def test_get_single_case_invalid_case_id(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt_(request):
        return {
            "sub": "mock-admin-id",
            "username": "admin_user",
            "role": "ADMIN"
        }

    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt_
    )

    response = client.post(
        "/api/getSingleCase",
        json={"CaseID": "not-a-valid-uuid"}
    )

    assert response.status_code == 400
    #assert response.json()==""
    assert response.json()["detail"]["status"] == "error"

def test_get_single_case_not_found(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt_(request):
        return {
            "sub": "mock-admin-id",
            "username": "admin_user",
            "role": "ADMIN"
        }

    mock_connection = AsyncMock()
    mock_connection.fetchrow = AsyncMock(return_value=None)
    mock_connection.close = AsyncMock(return_value=None)

    mock_connect = AsyncMock(return_value=mock_connection)

    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt_
    )
    monkeypatch.setattr(
        cases_router.asyncpg, 
        "connect", 
        mock_connect
    )

    response = client.post(
        "/api/getSingleCase",
        json={"CaseID": "12345678-abcd-ef01-2345-6789abcdef01"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == {
        "status": "error",
        "message": "Case not found"
    }# Needed adjustment to properly assert HTTPException

    mock_connect.assert_called_once()
    mock_connection.fetchrow.assert_called_once()
    mock_connection.close.assert_called_once()

def test_get_single_case_admin_returns_case(monkeypatch):
    client.cookies.clear()

    def mock_verify_jwt_(request):
        return {
            "sub": "mock-admin-id",
            "username": "admin_user",
            "role": "ADMIN"
        }

    mock_minio_client = MagicMock()
    fake_case_id = "12345678-abcd-ef01-2345-6789abcdef01"
    fake_media_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    fake_report_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"
    fake_url = f"https://localhost:9000/images/{fake_media_id}.png"
    fake_annotations = [
        {"tag": "highlight", "cord": "15-35"},
        {"tag": "comment", "cord": "35-23"},
    ]

    fake_row = {
        "caseid": fake_case_id,
        "casecreator": "admin_user",
        "casename": "Flood in Durban",
        "casedescription": "Flood investigation case",
        "caseclosed": False,
        "casecreationdate": datetime(2026, 5, 20, 19, 43, 2, tzinfo=timezone.utc)
    }

    fake_evidence_rows = [
        {
            "reportid": fake_report_id,
            "mediaid": fake_media_id,
            "mediatitle": "123",
            "mediabucket": "images",
            "mediaextension": ".png",
            "mediatypeid": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "mediaurl": fake_url,
            "annotations": fake_annotations,
            "reportartifacts": {"ocr": "captured"},
            "reportfindings": "Flood watermark detected",
            "reportcomments": "Upload approved",
            "reportcertainty": 1,
            "reportdatecreation": datetime(2026, 5, 21, 8, 15, 0, tzinfo=timezone.utc)
        }
    ]

    mock_minio_client.generate_presigned_url.return_value = fake_url

    mock_connection = AsyncMock()
    mock_connection.fetchrow = AsyncMock(return_value=fake_row)
    mock_connection.fetch = AsyncMock(return_value=fake_evidence_rows)
    mock_connection.close = AsyncMock(return_value=None)

    mock_connect = AsyncMock(return_value=mock_connection)

    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt_
    )
    monkeypatch.setattr(
        cases_router.asyncpg, 
        "connect", 
        mock_connect
    )
    monkeypatch.setattr(
        cases_router.boto3, 
        "client", 
        MagicMock(return_value=mock_minio_client)
    )

    with patch("app.api.routers.cases_router.Case.get_comments", new_callable=AsyncMock) as mock_get_comments:
        mock_get_comments.return_value = []

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
            "caseDescription": "Flood investigation case",
            "caseClosed": False,
            "caseCreationDate": "2026-05-20T19:43:02+00:00"
        },
        "comments": [],
        "evidence": [
            {
                "reportId": fake_report_id,
                "mediaId": fake_media_id,
                "mediaName": "123",
                "mediaBucket": "images",
                "mediaExtension": ".png",
                "mediaTypeId": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "mediaUrl": fake_url,
                "annotations": fake_annotations,
                "reportArtifacts": {"ocr": "captured"},
                "reportCertainty": 1,
                "reportFindings": "Flood watermark detected",
                "reportComments": "Upload approved",
                "reportDateCreation": "2026-05-21T08:15:00+00:00"
            }
        ]
    }

def test_get_single_case_success_for_a_normal_user(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt_(request):
        return {
            "sub": "mock-user-id",
            "username": "standard_user",
            "role": "USER"
        }

    case_uuid = uuid4()
    report_uuid = uuid4()
    media_uuid = uuid4()
    media_type_uuid = uuid4()

    mock_case_row = {
        "casecreator": "investigator1",
        "casename": "Public Closed Case",
        "casedescription": "Visible to standard users",
        "caseid": case_uuid,
        "caseclosed": True,
        "casecreationdate": datetime.now(timezone.utc),
    }

    mock_evidence_row = {
        "reportid": report_uuid,
        "caseid": case_uuid,
        "mediaid": media_uuid,
        "reportartifacts": [],
        "mediatitle": "Sample Evidence",
        "reportfindings": "Sample Findings",
        "reportcomments": "Sample Comments",
        "reportdatecreation": datetime.now(timezone.utc),
        "mediatypeid": media_type_uuid,
        "mediabucket": "evidence-bucket",
        "mediaextension": ".jpg",
        "reportcertainty": None,
        "annotations": [],
    }

    mock_connection = AsyncMock()
    mock_connection.fetchrow = AsyncMock(return_value=mock_case_row)
    mock_connection.fetch = AsyncMock(return_value=[mock_evidence_row])
    mock_connection.close = AsyncMock(return_value=None)
    mock_connect = AsyncMock(return_value=mock_connection)

    monkeypatch.setattr("app.core.cases.Case.get_comments", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        cases_router,
        "verify_jwt", 
        mock_verify_jwt_
    )
    monkeypatch.setattr(
        cases_router.asyncpg,
        "connect", 
        mock_connect
    )

    response = client.post(
        "/api/getSingleCase",
        json={"CaseID": str(case_uuid)}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    assert data["evidence"][0]["mediaUrl"] == ""

def test_close_case_user_unauthorized(monkeypatch):
    client.cookies.clear()

    def mock_verify_jwt(request):
        return {
            "sub": "mock-user-id",
            "username": "normal_user",
            "role": "USER"
        }

    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )

    response = client.post(
        "/api/closeCase",
        json={"CaseID": "12345678-abcd-ef01-2345-6789abcdef01"}
    )

def test_close_case_not_found(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt(request):
        return {
            "sub": "mock-investigator-id",
            "username": "investigator_user",
            "role": "INVESTIGATOR"
        }
    
    mock_connection = AsyncMock()
    mock_connection.fetchrow = AsyncMock(return_value=None)
    mock_connection.close = AsyncMock(return_value=None)

    mock_connect = AsyncMock(return_value=mock_connection)

    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )
    monkeypatch.setattr(
        cases_router.asyncpg, 
        "connect", 
        mock_connect
    )

    response = client.post(
        "/api/closeCase",
        json={"CaseID": "12345678-abcd-ef01-2345-6789abcdef01"}
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Case not found or user unauthorized."
        }
    }

    mock_connect.assert_called_once()
    mock_connection.fetchrow.assert_called_once()
    mock_connection.close.assert_called_once()

def test_close_case_not_case_creator(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt(request):
        return {
            "sub": "mock-investigator-id",
            "username": "different_user",
            "role": "INVESTIGATOR"
        }

    mock_connection = AsyncMock()
    mock_connection.fetchrow = AsyncMock(return_value=None)
    mock_connection.close = AsyncMock(return_value=None)

    mock_connect = AsyncMock(return_value=mock_connection)

    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )
    monkeypatch.setattr(
        cases_router.asyncpg, 
        "connect", 
        mock_connect
    )

    response = client.post(
        "/api/closeCase",
        json={"CaseID": "12345678-abcd-ef01-2345-6789abcdef01"}
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Case not found or user unauthorized."
        }
    }

    mock_connect.assert_called_once()
    mock_connection.fetchrow.assert_called_once()
    mock_connection.close.assert_called_once()

def test_close_case_success_investigator(monkeypatch):
    client.cookies.clear()
    def mock_verify_jwt(request):
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

    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )
    monkeypatch.setattr(
        cases_router.asyncpg, 
        "connect", 
        mock_connect
    )

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
    def mock_verify_jwt(request):
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

    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )
    monkeypatch.setattr(
        cases_router.asyncpg, 
        "connect", 
        mock_connect
    )

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
    def mock_verify_jwt(request):
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

    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )
    monkeypatch.setattr(
        cases_router.asyncpg, 
        "connect", 
        mock_connect
    )

    response = client.post(
        "/api/closeCase",
        json={"CaseID": fake_case_id}
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Case not found or user unauthorized."
        }
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

def _mock_jwt_success(monkeypatch, *, sub="mock-investigator-id", username="investigator_user", role="INVESTIGATOR"):
    def mock_verify_jwt(request):
        return {"sub": sub, "username": username, "role": role}
    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )

def _mock_jwt_failure(monkeypatch, message):
    def mock_verify_jwt(request):
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error",
                "message": message
            }
        )

    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )

def _mock_db_connect(monkeypatch, *, fetchrow_return=None):
    mock_connection = AsyncMock()
    mock_connection.fetchrow = AsyncMock(return_value=fetchrow_return)
    mock_connection.close = AsyncMock(return_value=None)
    mock_connect = AsyncMock(return_value=mock_connection)
    monkeypatch.setattr(
        cases_router.asyncpg, 
        "connect", 
        mock_connect
    )
    return mock_connection, mock_connect

def test_update_case_missing_jwt(monkeypatch):
    client.cookies.clear()
    _mock_jwt_failure(monkeypatch, NOT_AUTH)

    response = client.post("/api/updateCase", json={})

    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": NOT_AUTH
        }
    }

def test_update_case_invalid_jwt(monkeypatch):
    client.cookies.clear()
    _mock_jwt_failure(monkeypatch, "Invalid token")

    response = client.post(
        "/api/updateCase",
        json={"CaseID": "12345678-abcd-ef01-2345-6789abcdef01"}
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": INVALID_TOKEN
        }
    }

def test_update_case_user_unauthorized(monkeypatch):
    client.cookies.clear()
    _mock_jwt_success(monkeypatch, sub="mock-user-id", username="normal_user", role="USER")

    response = client.post(
        "/api/updateCase",
        json={"CaseID": "12345678-abcd-ef01-2345-6789abcdef01"}
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": cases_router.USER_UNAUTHORIZED
        }
    }

def test_update_case_missing_case_id(monkeypatch):
    client.cookies.clear()
    _mock_jwt_success(monkeypatch)

    response = client.post(
        "/api/updateCase",
        json={}
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": cases_router.CASE_ID_REQUIRED
        }
    }

def test_update_case_invalid_case_id(monkeypatch):
    client.cookies.clear()
    _mock_jwt_success(monkeypatch)

    response = client.post(
        "/api/updateCase",
        json={"CaseID": "not-a-valid-uuid"}
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "'not-a-valid-uuid' is not a valid UUID format"
        }
    }

def test_update_case_no_fields_provided(monkeypatch):
    #Here we are testing for errors when CaseName and CaseDescription are None
    client.cookies.clear()
    _mock_jwt_success(monkeypatch)

    response = client.post(
        "/api/updateCase",
        json={"CaseID": "12345678-abcd-ef01-2345-6789abcdef01"}
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": cases_router.UPDATE_FIELDS_REQUIRED
        }
    }

#when case name is CaseName" ""
def test_update_case_invalid_name_blank(monkeypatch):
    client.cookies.clear()
    _mock_jwt_success(monkeypatch)

    response = client.post(
        "/api/updateCase",
        json={
            "CaseID": "12345678-abcd-ef01-2345-6789abcdef01",
            "CaseName": ""
        }
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "CaseName is required"
        }
    }

def test_update_case_name_too_long(monkeypatch):
    client.cookies.clear()
    _mock_jwt_success(monkeypatch)

    long_name = "A" * 256

    response = client.post(
        "/api/updateCase",
        json={
            "CaseID": "12345678-abcd-ef01-2345-6789abcdef01",
            "CaseName": long_name
        }
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "CaseName must be 255 characters or less"
        }
    }

def test_update_case_not_found(monkeypatch):
    client.cookies.clear()
    _mock_jwt_success(monkeypatch)
    mock_connection, mock_connect = _mock_db_connect(monkeypatch, fetchrow_return=None)

    response = client.post(
        "/api/updateCase",
        json={"CaseID": "12345678-abcd-ef01-2345-6789abcdef01", "CaseName": "Updated Case Name"}
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": cases_router.CASE_NOT_FOUND_OR_UNAUTHORIZED
        }
    }

    mock_connect.assert_called_once()
    mock_connection.fetchrow.assert_called_once()
    mock_connection.close.assert_called_once()

def test_update_case_not_case_creator(monkeypatch):
    client.cookies.clear()
    _mock_jwt_success(monkeypatch, username="different_user")
    mock_connection, mock_connect = _mock_db_connect(monkeypatch, fetchrow_return=None)

    response = client.post(
        "/api/updateCase",
        json={"CaseID": "12345678-abcd-ef01-2345-6789abcdef01", "CaseName": "Updated Case Name"}
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": cases_router.CASE_NOT_FOUND_OR_UNAUTHORIZED
        }
    }

    mock_connect.assert_called_once()
    mock_connection.fetchrow.assert_called_once()
    mock_connection.close.assert_called_once()

def test_update_case_success_name_only(monkeypatch):
    client.cookies.clear()
    _mock_jwt_success(monkeypatch)

    fake_case_id = "12345678-abcd-ef01-2345-6789abcdef01"
    fake_row = {"caseid": fake_case_id}

    mock_connection, mock_connect = _mock_db_connect(monkeypatch, fetchrow_return=fake_row)

    response = client.post(
        "/api/updateCase",
        json={
            "CaseID": fake_case_id,
            "CaseName": "Updated Case Name"
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Case updated successfully."
    }

def test_update_case_success_description_only(monkeypatch):
    client.cookies.clear()
    _mock_jwt_success(monkeypatch)

    fake_case_id = "12345678-abcd-ef01-2345-6789abcdef01"
    fake_row = {"caseid": fake_case_id}

    mock_connection, mock_connect = _mock_db_connect(monkeypatch, fetchrow_return=fake_row)

    response = client.post(
        "/api/updateCase",
        json={
            "CaseID": fake_case_id,
            "CaseDescription": "Updated Case Description"
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Case updated successfully."
    }

def test_update_case_database_error(monkeypatch):
    client.cookies.clear()
    _mock_jwt_success(monkeypatch)
    mock_connection, mock_connect = _mock_db_connect(monkeypatch)
    mock_connection.fetchrow = AsyncMock(side_effect=asyncpg.PostgresError("boom"))

    response = client.post(
        "/api/updateCase",
        json={"CaseID":"12345678-abcd-ef01-2345-6789abcdef01", "CaseName": "Updated Case Name"}
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": cases_router.DATABASE_ERROR_MESSAGE
        }
    }

    mock_connection.close.assert_called_once()

@pytest.mark.asyncio
async def test_get_comment_missing_case_id():
    """
    Verifies that the case.get_comments(self) will throw an error if there is no caseId defined
    """
    test_case=Case(
        case_creator="Billy Jean",
        case_name="Billy Jean's not my Son"
    )

    with pytest.raises(HTTPException) as exeInfo:
        await test_case.get_comments()

    assert exeInfo.value.status_code == 400
    assert "Case id is missing" in exeInfo.value.detail  

@pytest.mark.asyncio
async def test_get_comment_successful():
    """
Return a dict of the comments belonging to the case id
    """
    #Enter a random fake number for the case id
    fake_id = uuid4()
    fake_case_id=str(fake_id)
    fake_record=[{
        "commentID": "1",
        "username": "Billy Jean",
        "comment": "I am your child",
        "commenttimestamp":"2026-06-29 15:37:28.458993+00"
    }]

    mock_connection = AsyncMock()
    mock_connection.fetch.return_value = fake_record
    
    test_case = Case(
        case_id=fake_case_id
    )

    with patch("app.core.cases.asyncpg.connect", new_callable=AsyncMock) as mock_connect:
        mock_connect.return_value = mock_connection

        result = await test_case.get_comments()

    assert isinstance(result, list), "Should be a single returned record"
    assert result[0]["commentID"] == "1"
    assert len(result) == 1
    assert result[0]["username"] == "Billy Jean"
    assert result[0]["comment"] == "I am your child"
    assert result[0]["commenttimestamp"]=="2026-06-29 15:37:28.458993+00"

    mock_connection.fetch.assert_called_once()
    called_args = mock_connection.fetch.call_args[0]
    assert called_args[1] == str(fake_id)

@pytest.mark.asyncio
async def test_get_comment_database_error():
    """
Raises an error due to the database going down
    """
    #Enter a random fake number for the case id
    fake_id = uuid4()
    fake_case_id=str(fake_id)
    

    test_case=Case(
        case_id=fake_case_id
    )

    with patch("app.core.cases.asyncpg.connect", new_callable=AsyncMock) as mock_connect:
        mock_connect.side_effect = asyncpg.PostgresConnectionError("Connection lost")

        with pytest.raises(HTTPException) as exc_info:
            await test_case.get_comments()

    assert exc_info.value.status_code == 500
    assert "Internal Server Error" in exc_info.value.detail or "database" in exc_info.value.detail.lower()


def test_delete_case_success_creator(monkeypatch):
    client.cookies.clear()

    def mock_verify_jwt(request):
        return {
            "sub": "mock-user-id",
            "username": "investigator_user",
            "role": "INVESTIGATOR"
        }
    
    async def mock_delete_case(self, username: str, role: str):
        assert isinstance(self.case_id, str)
        assert self.case_id == "12345678-abcd-ef01-2345-6789abcdef01"
        assert username == "investigator_user"
        assert role == "INVESTIGATOR"
    
        return None
    
    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )
    monkeypatch.setattr(
        cases_router.Case, 
        "delete_case", 
        mock_delete_case
    )

    response = client.request(
        "DELETE",
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

    def mock_verify_jwt(request):
        return {
            "sub": "mock-admin-id",
            "username": "admin_user",
            "role": "ADMIN"
        }
    
    async def mock_delete_case(self, username: str, role: str):
        assert isinstance(self.case_id, str)
        assert self.case_id == "12345678-abcd-ef01-2345-6789abcdef01"
        assert username == "admin_user"
        assert role == "ADMIN"

        return None
    
    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )
    monkeypatch.setattr(
        cases_router.Case, 
        "delete_case", 
        mock_delete_case
    )

    response = client.request(
        "DELETE",
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

    def mock_verify_jwt(request):
        raise ValueError("Missing token")
    
    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )

    with pytest.raises(ValueError, match="Missing token"):
        client.request(
            "DELETE",
            "/api/deleteCase",
            json={
                "CaseID": "12345678-abcd-ef01-2345-6789abcdef01"
            }
        )

def test_delete_case_user_forbidden(monkeypatch):
    client.cookies.clear()

    def mock_verify_jwt(request):
        return {
            "sub": "mock-user-id",
            "username": "normal_user",
            "role": "USER"
        }
    
    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )
    
    response = client.request(
        "DELETE",
        "/api/deleteCase",
        json={
            "CaseID": "12345678-abcd-ef01-2345-6789abcdef01"
        }
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "User unauthorized"
        }
    }

def test_delete_case_missing_case_id(monkeypatch):
    client.cookies.clear()

    def mock_verify_jwt(request):
        return {
            "sub": "mock-investigator-id",
            "username": "investigator_user",
            "role": "INVESTIGATOR"
        }
    
    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )

    response = client.request(
        "DELETE",
        "/api/deleteCase",
        json={}
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "CaseID required"
        }
    }

def test_delete_case_invalid_case_id(monkeypatch):
    client.cookies.clear()

    def mock_verify_jwt(request):
        return {
            "sub": "mock-investigator-id",
            "username": "investigator_user",
            "role": "INVESTIGATOR"
        }
    
    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )

    response = client.request(
        "DELETE",
        "/api/deleteCase",
        json={
            "CaseID": "not-a-valid-uuid"
        }
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "'not-a-valid-uuid' is not a valid UUID format"
        }
    }

def test_delete_case_not_found(monkeypatch):
    client.cookies.clear()

    def mock_verify_jwt(request):
        return{
            "sub": "mock-investigator-id",
            "username": "investigator_user",
            "role": "INVESTIGATOR"
        }
    
    async def mock_delete_case(self, username: str, role: str):
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "message": "Case not found"
            }
        )
    
    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )
    monkeypatch.setattr(
        cases_router.Case, 
        "delete_case", 
        mock_delete_case
    )

    response = client.request(
        "DELETE",
        "/api/deleteCase",
        json={
            "CaseID": "12345678-abcd-ef01-2345-6789abcdef01"
        }
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Case not found"
        }
    }

def test_delete_case_unauthorized_non_creator(monkeypatch):
    client.cookies.clear()

    def mock_verify_jwt(request):
        return {
            "sub": "mock-investigator-id",
            "username": "other_investigator",
            "role": "INVESTIGATOR"
        }
    
    async def mock_delete_case(self, username: str, role: str):
        assert username == "other_investigator"
        assert role == "INVESTIGATOR"
        
        raise HTTPException(
            status_code=403,
            detail={
                "status": "error",
                "message": "Only the case creator or an admin can delete this case"
            }
        )
    
    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )
    monkeypatch.setattr(
        cases_router.Case, 
        "delete_case", 
        mock_delete_case
    )

    response = client.request(
        "DELETE",
        "/api/deleteCase",
        json={
            "CaseID": "12345678-abcd-ef01-2345-6789abcdef01"
        }
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Only the case creator or an admin can delete this case"
        }
    }

@pytest.mark.asyncio
async def test_add_comment_case_not_found():
    connection = AsyncMock()
    connection.fetchrow = AsyncMock(return_value=None)

    case = Case(case_creator="New_Dev", case_name="The Reciepts exposed")
    case.case_id = uuid4()

    with pytest.raises(HTTPException) as excInfo:
        await case.add_comment(connection, "someone", "comment_ig", "USER")

    assert excInfo.value.status_code == 404
    assert excInfo.value.detail == {
        "status": "error",
        "message": "Case not found"
    }

@pytest.mark.asyncio
async def test_add_comment_user_blocked_on_open_case():
    connection = AsyncMock()
    connection.fetchrow = AsyncMock(return_value={
        "commentid": None,
        "caseid": None,
        "username": None,
        "comment": None,
        "commenttimestamp": None,
        "caseclosed": False,
        "case_exists": True,
        "comment_inserted": False
    })

    case = Case(case_creator="New_Dev", case_name="The Reciepts exposed")
    case.case_id = uuid4()

    with pytest.raises(HTTPException) as excInfo:
        await case.add_comment(connection, "someone", "comment_ig", "USER")
        
    assert excInfo.value.status_code == 403
    assert excInfo.value.detail == {
        "status": "error",
        "message": "Users may only comment on closed cases"
    }

def make_mock_connection_with_transaction():
    connection = AsyncMock()
    transaction_cm = MagicMock()
    transaction_cm.__aenter__ = AsyncMock(return_value=None)
    transaction_cm.__aexit__ = AsyncMock(return_value=False)
    connection.transaction = MagicMock(return_value=transaction_cm)
    return connection

@pytest.mark.asyncio
@patch("asyncpg.connect")
async def test_delete_case_not_found(mockDbConnect):
    connection = make_mock_connection_with_transaction()
    mockDbConnect.return_value = connection

    connection.fetchrow = AsyncMock(return_value=None)

    case = Case(case_id=str(uuid4()))

    with pytest.raises(HTTPException) as excInfo:
        await case.delete_case("someone", "USER")

    assert excInfo.value.status_code == 404
    assert excInfo.value.detail == {
        "status": "error",
        "message": "Case not found"
    }
    connection.close.assert_called_once()

@pytest.mark.asyncio
@patch("asyncpg.connect")
async def test_delete_case_unauthorized(mockDbConnect):
    connection = make_mock_connection_with_transaction()
    mockDbConnect.return_value = connection

    connection.fetchrow = AsyncMock(return_value={"casecreator": "tha_real_creator"})

    case = Case(case_id=str(uuid4()))

    with pytest.raises(HTTPException) as excInfo:
        await case.delete_case("someone_eklse", "USER")

    assert excInfo.value.status_code == 403
    assert excInfo.value.detail == {
        "status": "error",
        "message": "Only the case creator or an admin can delete this case"
    }
    connection.close.assert_called_once()

@pytest.mark.asyncio
@patch("asyncpg.connect")
@patch("app.core.cases.get_object")
async def test_delete_case_success_with_orphan_media_cleanup(mockget_object, mockDbConnect):
    connection = make_mock_connection_with_transaction()
    mockDbConnect.return_value = connection

    case_id = uuid4()

    connection.fetchrow = AsyncMock(side_effect=[
        {"casecreator": "tha_real_creator"},
        {"caseid": case_id, "mediaids": ["media-1"]},
        {"mediaid": "media-1", "mediabucket": "evidence-bucket", "mediaextension": ".jpg" },
        ])

    mock_s3_client = MagicMock()
    mockget_object.return_value = mock_s3_client

    case = Case(case_id=str(case_id))

    result = await case.delete_case("tha_real_creator", "USER")

    assert result is None
    mock_s3_client.delete_object.assert_called_once_with(
        Bucket="evidence-bucket",
        Key="media-1.jpg"
    )
    connection.close.assert_called_once()

def test_get_comments_missing_jwt(monkeypatch):
    client.cookies.clear()

    def mock_verify_jwt(request):
        raise ValueError("Missing authorization header")

    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )

    with pytest.raises(ValueError) as excinfo:
        client.post("/api/getComments/12345678-abcd-ef01-2345-6789abcdef01")

    assert "Missing authorization header" in str(excinfo.value)


import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
import io
import uuid
import asyncpg
from botocore.exceptions import EndpointConnectionError

from app.api.main import app
from app.core.cases import (
    Case,
    UNSUPPORTED_EXTENSION_PREFIX,
    MEDIA_ALREADY_ON_CASE,
    PDF_SCRIPTS_NOT_ALLOWED,
    INVALID_CASE_ID_UUID,
    INTERNAL_SERVER_ERROR_STORAGE
)
import app.api.routers.cases_router as cases_router
from starlette.datastructures import UploadFile
from app.core.database import get_connection
from app.tests.unit.database_override import unit_get_connection


client = TestClient(app)


@pytest.fixture(autouse=True)
def override_database_dependency():
    app.dependency_overrides[get_connection] = unit_get_connection
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_connection, None)


@pytest.mark.asyncio
@patch("asyncpg.connect")
@patch("app.core.cases.get_object")
@patch("uuid.uuid4")
async def test_images_upload_success(mockUuid, mockget_object, mockDbConnect):
    """
    Test successful evidence processing and extension identification
    """
    fileContent = b"A fake binary for a png"
    testContent = io.BytesIO(fileContent)
    
    mockMedia = UploadFile(
        file=testContent,
        filename="success.png",
        headers={"content-type": "image/png"}
    )

    fakeUuidString = "22222222-abcd-ef01-2345-6789abcdef01"
    mockUuid.return_value = fakeUuidString

    mockDbConnection = AsyncMock()
    mockDbConnect.return_value = mockDbConnection

    mockMediaTypeRecord = {
        "MediaTypeId": "type-111", 
        "MediaBucket": "images",
        "MediaExtension": ".png"
    }

    # fetchrow is called twice: first for media type, second to check existing media
    # For successful upload, second call should return None (media doesn't exist yet)
    mockDbConnection.fetchrow = AsyncMock(side_effect=[mockMediaTypeRecord, None])
    mockDbConnection.fetchval = AsyncMock(return_value="mocked-evidence-uuid-123")
    mockDbConnection.execute = AsyncMock()
    mockDbConnection.close = AsyncMock()

    mockStorageClient = MagicMock()
    mockStorageClient.put_object = MagicMock()
    mockStorageClient.generate_presigned_url = MagicMock(return_value="https://example.com/fake-url")
    mockget_object.return_value = mockStorageClient

    case = Case(case_creator="New_Dev", case_name="The Jones v Smith")
    test_case_id = uuid.uuid4()

    result = await case.add_evidence(media=mockMedia, case_id=test_case_id, connection=mockDbConnection)

    # Verify the result
    assert result is not None
    assert "url" in result


@pytest.mark.asyncio
@patch("asyncpg.connect")
async def test_invalid_file_type(mockDbConnect):
    """Test that a rubbish file format throws a clean 400 error"""
    fileContent = b"some random junk text data matching food"
    testContent = io.BytesIO(fileContent)

    mockMedia = UploadFile(
        file=testContent,
        filename="hangry.food",
        headers={"content-type": "application/octet-stream"}
    )

    mockDbConnection = AsyncMock()
    mockDbConnect.return_value = mockDbConnection

    mockDbConnection.fetchrow.return_value = None
    mockDbConnection.close = AsyncMock()

    case = Case(case_creator="New_Dev", case_name="The Jones v Smith")
    test_case_id = uuid.uuid4()

    with pytest.raises(HTTPException) as excInfo:
        await case.add_evidence(media=mockMedia, case_id=test_case_id, connection=mockDbConnection)

    assert excInfo.value.status_code == 400
    assert excInfo.value.detail["message"] == f"{UNSUPPORTED_EXTENSION_PREFIX}.food"



@pytest.mark.asyncio
@patch("asyncpg.connect")
@patch("app.core.cases.get_object")
@patch("uuid.uuid4")
async def test_same_image_different_name(mockUuid, mockget_object, mockDbConnect):
    """
    Testing the image hash for dupe  prevention
    """
    fileContent = b"A fake binary for a png"
    
    # First upload: success.png
    testContent1 = io.BytesIO(fileContent)
    mockMedia1 = UploadFile(
        file=testContent1,
        filename="success.png",
        headers={"content-type": "image/png"}
    )
    
    # Second upload: same content but different filename
    testContent2 = io.BytesIO(fileContent)
    mockMedia2 = UploadFile(
        file=testContent2,
        filename="success-copy.png",
        headers={"content-type": "image/png"}
    )

    fakeUuidString = "22222222-abcd-ef01-2345-6789abcdef01"
    mockUuid.return_value = fakeUuidString

    mockDbConnection = AsyncMock()
    mockDbConnect.return_value = mockDbConnection

    mockMediaTypeRecord = {
        "MediaTypeId": "type-111", 
        "MediaBucket": "images",
        "MediaExtension": ".png"
    }
    
    existingMediaRecord = {
        "MediaId": "mocked-evidence-uuid-123"
    }

    mockDbConnection.fetchrow = AsyncMock(
        side_effect=[mockMediaTypeRecord, None, mockMediaTypeRecord, existingMediaRecord]
    )
    mockDbConnection.fetchval = AsyncMock(return_value="mocked-evidence-uuid-123")
    mockDbConnection.execute = AsyncMock()
    mockDbConnection.close = AsyncMock()

    mockStorageClient = MagicMock()
    mockStorageClient.put_object = MagicMock()
    mockStorageClient.generate_presigned_url = MagicMock(return_value="https://example.com/fake-url")
    mockget_object.return_value = mockStorageClient

    case = Case(case_creator="New_Dev", case_name="The Jones v Smith")
    test_case_id_1 = uuid.uuid4()
    test_case_id_2 = uuid.uuid4()

    result1 = await case.add_evidence(media=mockMedia1, case_id=test_case_id_1, connection=mockDbConnection)
    
    result2 = await case.add_evidence(media=mockMedia2, case_id=test_case_id_2, connection=mockDbConnection)

    assert result1 is not None
    assert "url" in result1
    assert result2 is not None
    assert "url" in result2
    
    # Verify first upload shows as "uploaded" (new media)
    assert result1.get("Status") == "uploaded", "First upload should mark media as uploaded"
    
    # Verify second upload shows as "existing" (duplicate detected via hash)
    assert result2.get("Status") == "existing", "Second upload should detect existing media via hash deduplication"
    
    # Verify the URLs are the same (same file, same link)
    assert result1.get("url") == result2.get("url"), "Same file with different names should return the same URL"


@pytest.mark.asyncio
@patch("asyncpg.connect")
@patch("app.core.cases.get_object")
@patch("uuid.uuid4")
async def test_duplicate_report_violates_constraint(mockUuid, mockget_object, mockDbConnect):
    """
    Test uniqueness error handling when dupes in same case appear
    """
    fileContent = b"A fake binary for a png"
    
    # First upload: success.png
    testContent1 = io.BytesIO(fileContent)
    mockMedia1 = UploadFile(
        file=testContent1,
        filename="success.png",
        headers={"content-type": "image/png"}
    )
    
    # Second upload: same content and same case
    testContent2 = io.BytesIO(fileContent)
    mockMedia2 = UploadFile(
        file=testContent2,
        filename="success-copy.png",
        headers={"content-type": "image/png"}
    )

    fakeUuidString = "22222222-abcd-ef01-2345-6789abcdef01"
    mockUuid.return_value = fakeUuidString

    mockDbConnection = AsyncMock()
    mockDbConnect.return_value = mockDbConnection

    mockMediaTypeRecord = {
        "MediaTypeId": "type-111", 
        "MediaBucket": "images",
        "MediaExtension": ".png"
    }
    
    existingMediaRecord = {
        "MediaId": "mocked-evidence-uuid-123"
    }

    mockDbConnection.fetchrow = AsyncMock(
        side_effect=[mockMediaTypeRecord, None, mockMediaTypeRecord, existingMediaRecord]
    )
    mockDbConnection.fetchval = AsyncMock(return_value="mocked-evidence-uuid-123")
    
    # First execute succeeds, second execute throws UniqueViolationError 
    mockDbConnection.execute = AsyncMock(
        side_effect=[
            None,  # First insert succeeds
            asyncpg.exceptions.UniqueViolationError("Duplicate key value violates unique constraint")
        ]
    )
    mockDbConnection.close = AsyncMock()

    mockStorageClient = MagicMock()
    mockStorageClient.put_object = MagicMock()
    mockStorageClient.generate_presigned_url = MagicMock(return_value="https://example.com/fake-url")
    mockget_object.return_value = mockStorageClient

    case = Case(case_creator="New_Dev", case_name="The Jones v Smith")
    test_case_id = uuid.uuid4()

    result1 = await case.add_evidence(media=mockMedia1, case_id=test_case_id, connection=mockDbConnection)
    assert result1 is not None
    assert result1.get("Status") == "uploaded"
    
    # Second upload should raise HTTPException with 409 Conflict
    with pytest.raises(HTTPException) as excInfo:
        await case.add_evidence(media=mockMedia2, case_id=test_case_id, connection=mockDbConnection)
    
    assert excInfo.value.status_code == 409
    assert excInfo.value.detail["message"] == MEDIA_ALREADY_ON_CASE

#Tests for deleting the Evidence

@pytest.mark.asyncio
@patch("asyncpg.connect")
@patch("app.core.cases.get_object")
async def test_delete_evidence_investigator_duplicate_entry(mockget_object, mockDbConnect):
    """
An investigator deletes a duplicate. Only the report is deleted.
    """
    mockDbConnection = AsyncMock()
    mockDbConnection.transaction = MagicMock()
    mockDbConnect.return_value = mockDbConnection

    mockDbConnection.execute = AsyncMock(return_value="DELETE 1")
    mockDbConnection.fetchrow = AsyncMock(return_value=None)
    mockDbConnection.close = AsyncMock()

    mock_s3_client = MagicMock()
    mockget_object.return_value = mock_s3_client

    case = Case(case_creator="New_Dev", case_name="The Jones v Smith")
    case.case_id = uuid.uuid4()
    test_media_id = uuid.uuid4()
    test_user = "Investigator_Bob"

    result = await case.delete_evidence(media_id=test_media_id, jwt_username=test_user, connection=mockDbConnection)

    mockDbConnection.execute.assert_called_once()
    mock_s3_client.remove_object.assert_not_called()
    assert result["status"] == "success"
    assert result["deleted"] == test_media_id


@pytest.mark.asyncio
@patch("asyncpg.connect")
@patch("app.core.cases.get_object")
@patch("app.core.cases.asyncio", create=True)
async def test_delete_evidence_investigator_only_entry(mock_asyncio, mockget_object, mockDbConnect):
    """
An investigator deletes the only entry for that evidence.The report is deleted and the same for the Minio.
    """
    mockDbConnection = AsyncMock()
    mockDbConnection.transaction = MagicMock()
    mockDbConnect.return_value = mockDbConnection

    mockMediaData = {
        "mediaid": "mocked-uuid",
        "mediabucket": "evidence-bucket",
        "mediaextension": ".jpg"
    }

    mockDbConnection.execute = AsyncMock(return_value="DELETE 1")
    mockDbConnection.fetchrow = AsyncMock(return_value=mockMediaData)
    mockDbConnection.close = AsyncMock()
    mock_asyncio.to_thread = AsyncMock()

    mock_s3_client = MagicMock()
    mockget_object.return_value = mock_s3_client

    case = Case(case_creator="New_Dev", case_name="The Jones v Smith")
    case.case_id = uuid.uuid4()
    test_media_id = uuid.uuid4()
    test_user = "Investigator_Bob"

    result = await case.delete_evidence(media_id=test_media_id, jwt_username=test_user, connection=mockDbConnection)

    mock_asyncio.to_thread.assert_awaited_once_with(
        mock_s3_client.delete_object,
        Bucket="evidence-bucket",
        Key="mocked-uuid.jpg"
    )
    assert result["status"] == "success"


@pytest.mark.asyncio
@patch("asyncpg.connect")
@patch("app.core.cases.get_object")
async def test_delete_evidence_admin_duplicate_entry(mockget_object, mockDbConnect):
    """
An admin deletes a duplicate. Therefore only the report is deleted
    """
    mockDbConnection = AsyncMock()
    mockDbConnection.transaction = MagicMock()
    mockDbConnect.return_value = mockDbConnection

    mockDbConnection.execute = AsyncMock(return_value="DELETE 1")
    mockDbConnection.fetchrow = AsyncMock(return_value=None)

    mock_s3_client = MagicMock()
    mockget_object.return_value = mock_s3_client

    case = Case(case_creator="New_Dev", case_name="The Jones v Smith")
    case.case_id = uuid.uuid4()
    test_media_id = uuid.uuid4()
    
    result = await case.delete_evidence(media_id=test_media_id, connection=mockDbConnection)

    mockDbConnection.execute.assert_called_once()
    mock_s3_client.remove_object.assert_not_called()
    assert result["status"] == "success"


@pytest.mark.asyncio
@patch("asyncpg.connect")
@patch("app.core.cases.get_object")
@patch("app.core.cases.asyncio", create=True)
async def test_delete_evidence_admin_only_entry(mock_asyncio, mockget_object, mockDbConnect):
    """
An admin deletes the only entry of that evidence. The Minio version is deleted and the report is also deleted
    """
    mockDbConnection = AsyncMock()
    mockDbConnection.transaction = MagicMock()
    mockDbConnect.return_value = mockDbConnection

    mockMediaData = {
        "mediaid": "admin-mocked-uuid",
        "mediabucket": "evidence-bucket",
        "mediaextension": ".png"
    }

    mockDbConnection.execute = AsyncMock(return_value="DELETE 1")
    mockDbConnection.fetchrow = AsyncMock(return_value=mockMediaData)
    mock_asyncio.to_thread = AsyncMock()

    mock_s3_client = MagicMock()
    mockget_object.return_value = mock_s3_client

    case = Case(case_creator="New_Dev", case_name="The Jones v Smith")
    case.case_id = uuid.uuid4()
    test_media_id = uuid.uuid4()
    
    result = await case.delete_evidence(media_id=test_media_id, connection=mockDbConnection)

    mock_asyncio.to_thread.assert_awaited_once_with(
        mock_s3_client.delete_object,
        Bucket="evidence-bucket",
        Key="admin-mocked-uuid.png"
    )
    assert result["status"] == "success"

@pytest.mark.asyncio
async def test_delete_evidence_missing_case_id_400():
    """
    A missing Media_id should raise an exception
    """
    case = Case(case_creator="New_Dev", case_name="The Jones v Smith")
    case.case_id = None

    test_media_id = uuid.uuid4()
    test_user = "Investigator_Bob"
    mockDbConnection = AsyncMock()

    with pytest.raises(HTTPException) as excInfo:
        await case.delete_evidence(media_id=test_media_id, jwt_username=test_user, connection=mockDbConnection)

    assert excInfo.value.status_code == 400
    assert excInfo.value.detail == {
        "status": "error", 
        "message": "Case id is missing"
    }

@pytest.mark.asyncio
@patch("asyncpg.connect")
async def test_delete_evidence_investigator_unauthorized_403(mockDbConnect):
    """
An investigator tries to delete evidence but it fails due to either CaseCreator validation or record is missing (returns DELETE 0). Should raise 403.
    """
    mockDbConnection = AsyncMock()
    mockDbConnection.transaction = MagicMock()
    mockDbConnect.return_value = mockDbConnection

    mockDbConnection.execute = AsyncMock(return_value="DELETE 0")
    
    case = Case(case_creator="New_Dev", case_name="The Jones v Smith")
    case.case_id = uuid.uuid4()
    test_media_id = uuid.uuid4()
    test_user = "Hacker_Eve"

    with pytest.raises(HTTPException) as excInfo:
        await case.delete_evidence(media_id=test_media_id, jwt_username=test_user, connection=mockDbConnection)

    assert excInfo.value.status_code == 403
    assert excInfo.value.detail["message"] == "Unauthorized to delete this evidence or record not found."


@pytest.mark.asyncio
@patch("asyncpg.connect")
async def test_delete_evidence_admin_not_found_404(mockDbConnect):
    """
When an admin tries to delete a record that does not exist. (returns DELETE 0). Should raise 404.
    """
    mockDbConnection = AsyncMock()
    mockDbConnection.transaction = MagicMock()
    mockDbConnect.return_value = mockDbConnection

    mockDbConnection.execute = AsyncMock(return_value="DELETE 0")
    
    case = Case(case_creator="New_Dev", case_name="The Jones v Smith")
    case.case_id = uuid.uuid4()
    test_media_id = uuid.uuid4()

    with pytest.raises(HTTPException) as excInfo:
        await case.delete_evidence(media_id=test_media_id, connection=mockDbConnection)

    assert excInfo.value.status_code == 404
    assert excInfo.value.detail == {"status": "error", "message": "Media not found."}


@pytest.mark.asyncio
@patch("app.core.cases.PdfReader")
async def test_add_evidence_pdf_open_action_rejected(mockPdfReaderClass):
    fileContent = b"fake pdf bytes"
    testContent = io.BytesIO(fileContent)

    mockMedia = UploadFile(
        file=testContent,
        filename="system_danger.pdf",
        headers={"content-type": "application/pdf"}
    )

    mockRootIndirect = MagicMock()
    mockRootIndirect.get_object.return_value = {"/OpenAction": MagicMock()}

    mockReader = MagicMock()
    mockReader.trailer = {"/Root": mockRootIndirect}
    mockPdfReaderClass.return_value = mockReader

    case = Case(case_creator="New_Dev", case_name="The Reciepts exposed")
    test_case_id = uuid.uuid4()
    connection = AsyncMock()

    with pytest.raises(HTTPException) as excInfo:
        await case.add_evidence(media=mockMedia, case_id=test_case_id, connection=connection)

    assert excInfo.value.status_code == 400
    assert excInfo.value.detail["message"] == PDF_SCRIPTS_NOT_ALLOWED

@pytest.mark.asyncio
@patch("app.core.cases.PdfReader")
async def test_add_evidence_pdf_javascript_rejected(mockPdfReaderClass):
    fileContent = b"fake pdf bytes"
    testContent = io.BytesIO(fileContent)

    mockMedia = UploadFile(
        file=testContent,
        filename="scripted.pdf",
        headers={"content-type": "application/pdf"}
    )

    mockNamesIndirect = MagicMock()
    mockNamesIndirect.get_object.return_value = {"/JavaScript": MagicMock()}

    mockRootIndirect = MagicMock()
    mockRootIndirect.get_object.return_value = {"/Names": mockNamesIndirect}

    mockReader = MagicMock()
    mockReader.trailer = {"/Root": mockRootIndirect}
    mockPdfReaderClass.return_value = mockReader

    case = Case(case_creator="New_Dev", case_name="The Reciepts exposed")
    test_case_id = uuid.uuid4()
    connection = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await case.add_evidence(media=mockMedia, case_id=test_case_id, connection=connection)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["message"] == PDF_SCRIPTS_NOT_ALLOWED

@pytest.mark.asyncio
@patch("asyncpg.connect")
@patch("app.core.cases.get_object")
@patch("app.core.cases.PdfReader")
@patch("uuid.uuid4")
async def test_add_evidence_pdf_bengin_upload_success(mockUuid,mockPdfReaderClass, mockget_object, mockDbConnect):
    fileContent = b"fake pdf bytes"
    testContent = io.BytesIO(fileContent)

    mockMedia = UploadFile(
        file=testContent,
        filename="clean.pdf",
        headers={"content-type": "application/pdf"}
    )

    mockRootIndirect = MagicMock()
    mockRootIndirect.get_object.return_value = {}

    mockReader = MagicMock()
    mockReader.trailer = {"/Root": mockRootIndirect}
    mockPdfReaderClass.return_value = mockReader

    fakeUuidString = "33333333-abcd-ef01-2345-6789abcdef01"
    mockUuid.return_value = fakeUuidString

    mockDbConnection = AsyncMock()
    mockDbConnection.return_value = mockDbConnection

    mockMediaTypeRecord = {
        "MediaTypeId": "type-222",
        "MediaBucket": "documents",
        "MediaExtension": ".pdf"
    }

    mockDbConnection.fetchrow = AsyncMock(side_effect=[mockMediaTypeRecord, None])
    mockDbConnection.fetchval = AsyncMock(return_value="mocked-evidence-uuid-456")
    mockDbConnection.execute = AsyncMock()
    mockDbConnection.close = AsyncMock()

    mock_s3_client = MagicMock()
    mock_s3_client.generate_presigned_url.return_value = "https://fake-presigned-url"
    mockget_object.return_value = mock_s3_client

    case = Case(case_creator="New_Dev", case_name="The Reciepts exposed")
    test_case_id = uuid.uuid4()

    result = await case.add_evidence(media=mockMedia, case_id=test_case_id, connection=mockDbConnection)

    assert result is not None 
    assert result["url"] == "https://fake-presigned-url"

def test_delete_evidence_missing_jwt(monkeypatch):
    client.cookies.clear()

    def mock_verify_jwt(request):
        raise HTTPException(
            status_code=401,
            detail={"status": "error", "message": "Missing authorization header"}
        )

    monkeypatch.setattr(
        cases_router,
        "verify_jwt",
        mock_verify_jwt
    )

    response = client.post(
        "/api/delete/case/12345678-abcd-ef01-2345-6789abcdef01/evidence/22222222-abcd-ef01-2345-6789abcdef01"
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Missing authorization header"
        }
    }

def test_delete_evidence_success(monkeypatch):
    client.cookies.clear()

    def mock_verify_jwt(request):
        return {
            "sub": "admin-id",
            "username": "admin_user",
            "role": "ADMIN"
        }

    fake_result = {
        "Status": "success",
        "Deleted": "22222222-abcd-ef01-2345-6789abcdef01"
    }

    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )
    monkeypatch.setattr(
        cases_router.Case, 
        "delete_evidence", 
        AsyncMock(return_value=fake_result)
    )

    response = client.post(
        "/api/delete/case/12345678-abcd-ef01-2345-6789abcdef01/evidence/22222222-abcd-ef01-2345-6789abcdef01"
    )

    assert response.status_code == 200
    assert response.json() == fake_result

def test_delete_evidence_invalid_media_id(monkeypatch):
    client.cookies.clear()

    def mock_verify_jwt(request):
        return {
            "sub": "admin-id",
            "username": "admin_user",
            "role": "ADMIN"
        }

    monkeypatch.setattr(
        cases_router,
        "verify_jwt",
        mock_verify_jwt
    )

    response = client.post(
        "/api/delete/case/12345678-abcd-ef01-2345-6789abcdef01/evidence/not-a-valid-uuid"
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Media is an invalid uuid"
        }
    }

def test_delete_evidence_user_forbidden(monkeypatch):
    client.cookies.clear()

    def mock_verify_jwt(request):
        return {
            "sub": "user-id",
            "username": "some_user",
            "role": "USER"
        }

    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )

    response = client.post(
        "/api/delete/case/12345678-abcd-ef01-2345-6789abcdef01/evidence/22222222-abcd-ef01-2345-6789abcdef01"
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "User unauthorized"
        }
    }

@pytest.mark.asyncio
@patch("app.core.cases.get_object")
@patch("asyncpg.connect")
async def test_add_evidence_storage_failure_returns_500(mockDbConnect, mockget_object):
    fileContent = b"A fake binary for a png"
    testContent = io.BytesIO(fileContent)

    mockMedia = UploadFile(
        file=testContent,
        filename="storage_fail.png",
        headers={"content-type": "image/png"}
    )

    mockMediaTypeRecord = {
        "MediaTypeId": "type-111", 
        "MediaBucket": "images",
        "MediaExtension": ".png"
    }

    mockDbConnection = AsyncMock()
    mockDbConnect.return_value = mockDbConnection
    mockDbConnection.fetchrow = AsyncMock(return_value=mockMediaTypeRecord)
    mockDbConnection.close = AsyncMock()

    mockget_object.side_effect = EndpointConnectionError(
        endpoint_url="http://minio:9000",
    )

    case = Case(case_creator="New_Dev", case_name="The Jones v Smith")
    test_case_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await case.add_evidence(media=mockMedia, case_id=test_case_id, connection=mockDbConnection)

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail["message"] == INTERNAL_SERVER_ERROR_STORAGE
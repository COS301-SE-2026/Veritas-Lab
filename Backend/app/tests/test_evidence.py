import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException
import io
import uuid
import asyncpg

from app.core.cases import Case
from starlette.datastructures import UploadFile


@pytest.mark.asyncio
@patch("asyncpg.connect")
@patch("app.core.cases.getObject")
@patch("uuid.uuid4")
async def test_images_Upload_Success(mockUuid, mockGetObject, mockDbConnect):
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
    mockGetObject.return_value = mockStorageClient

    case = Case(CaseCreator="New_Dev", CaseName="The Jones v Smith")
    test_case_id = uuid.uuid4()

    result = await case.addEvidence(media=mockMedia, case_id=test_case_id)

    # Verify the result
    assert result is not None
    assert "url" in result


@pytest.mark.asyncio
@patch("asyncpg.connect")
async def test_InvalidFileType(mockDbConnect):
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

    case = Case(CaseCreator="New_Dev", CaseName="The Jones v Smith")
    test_case_id = uuid.uuid4()

    with pytest.raises(HTTPException) as excInfo:
        await case.addEvidence(media=mockMedia, case_id=test_case_id)

    assert excInfo.value.status_code == 400
    assert "Unsupported file extension: .food" in excInfo.value.detail    

    mockDbConnection.close.assert_called_once()


@pytest.mark.asyncio
@patch("asyncpg.connect")
@patch("app.core.cases.getObject")
@patch("uuid.uuid4")
async def test_sameImageDifferentName(mockUuid, mockGetObject, mockDbConnect):
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
    mockGetObject.return_value = mockStorageClient

    case = Case(CaseCreator="New_Dev", CaseName="The Jones v Smith")
    test_case_id_1 = uuid.uuid4()
    test_case_id_2 = uuid.uuid4()

    result1 = await case.addEvidence(media=mockMedia1, case_id=test_case_id_1)
    
    result2 = await case.addEvidence(media=mockMedia2, case_id=test_case_id_2)

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
@patch("app.core.cases.getObject")
@patch("uuid.uuid4")
async def test_duplicateReportViolatesConstraint(mockUuid, mockGetObject, mockDbConnect):
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
    mockGetObject.return_value = mockStorageClient

    case = Case(CaseCreator="New_Dev", CaseName="The Jones v Smith")
    test_case_id = uuid.uuid4()

    result1 = await case.addEvidence(media=mockMedia1, case_id=test_case_id)
    assert result1 is not None
    assert result1.get("Status") == "uploaded"
    
    # Second upload should raise HTTPException with 409 Conflict
    with pytest.raises(HTTPException) as excInfo:
        await case.addEvidence(media=mockMedia2, case_id=test_case_id)
    
    assert excInfo.value.status_code == 409
    assert "already associated with this case" in excInfo.value.detail

#Tests for deleting the Evidence

@pytest.mark.asyncio
@patch("asyncpg.connect")
@patch("app.core.cases.getObject")
async def test_deleteEvidence_investigator_duplicate_entry(mockGetObject, mockDbConnect):
    """
An investigator deletes a duplicate. Only the report is deleted.
    """
    mockDbConnection = AsyncMock()
    mockDbConnect.return_value = mockDbConnection

    mockDbConnection.execute = AsyncMock(return_value="DELETE 1")
    mockDbConnection.fetchrow = AsyncMock(return_value=None)
    mockDbConnection.close = AsyncMock()

    mockStorageClient = MagicMock()
    mockGetObject.return_value = mockStorageClient

    case = Case(CaseCreator="New_Dev", CaseName="The Jones v Smith")
    case.CaseId = uuid.uuid4()
    test_media_id = uuid.uuid4()
    test_user = "Investigator_Bob"

    result = await case.deleteEvidence(media_id=test_media_id, JWT_username=test_user)

    mockDbConnection.execute.assert_called_once()
    mockStorageClient.delete_object.assert_not_called()
    assert result["Status"] == "success"
    assert result["Deleted"] == test_media_id


@pytest.mark.asyncio
@patch("asyncpg.connect")
@patch("app.core.cases.getObject")
async def test_deleteEvidence_investigator_only_entry(mockGetObject, mockDbConnect):
    """
An investigator deletes the only entry for that evidence.The report is deleted and the same for the Minio.
    """
    mockDbConnection = AsyncMock()
    mockDbConnect.return_value = mockDbConnection

    mockMediaData = {
        "mediaid": "mocked-uuid",
        "mediabucket": "evidence-bucket",
        "mediaextension": ".jpg"
    }

    mockDbConnection.execute = AsyncMock(return_value="DELETE 1")
    mockDbConnection.fetchrow = AsyncMock(return_value=mockMediaData)
    mockDbConnection.close = AsyncMock()

    mockStorageClient = MagicMock()
    mockGetObject.return_value = mockStorageClient

    case = Case(CaseCreator="New_Dev", CaseName="The Jones v Smith")
    case.CaseId = uuid.uuid4()
    test_media_id = uuid.uuid4()
    test_user = "Investigator_Bob"

    result = await case.deleteEvidence(media_id=test_media_id, JWT_username=test_user)

    mockStorageClient.delete_object.assert_called_once_with(
        Bucket="evidence-bucket",
        Key="mocked-uuid.jpg"
    )
    assert result["Status"] == "success"


@pytest.mark.asyncio
@patch("asyncpg.connect")
@patch("app.core.cases.getObject")
async def test_deleteEvidence_admin_duplicate_entry(mockGetObject, mockDbConnect):
    """
An admin deletes a duplicate. Therefore only the report is deleted
    """
    mockDbConnection = AsyncMock()
    mockDbConnect.return_value = mockDbConnection

    mockDbConnection.execute = AsyncMock(return_value="DELETE 1")
    mockDbConnection.fetchrow = AsyncMock(return_value=None)

    mockStorageClient = MagicMock()
    mockGetObject.return_value = mockStorageClient

    case = Case(CaseCreator="New_Dev", CaseName="The Jones v Smith")
    case.CaseId = uuid.uuid4()
    test_media_id = uuid.uuid4()
    
    result = await case.deleteEvidence(media_id=test_media_id)

    mockDbConnection.execute.assert_called_once()
    mockStorageClient.delete_object.assert_not_called()
    assert result["Status"] == "success"


@pytest.mark.asyncio
@patch("asyncpg.connect")
@patch("app.core.cases.getObject")
async def test_deleteEvidence_admin_only_entry(mockGetObject, mockDbConnect):
    """
An admin deletes the only entry of that evidence. The Minio version is deleted and the report is also deleted
    """
    mockDbConnection = AsyncMock()
    mockDbConnect.return_value = mockDbConnection

    mockMediaData = {
        "mediaid": "admin-mocked-uuid",
        "mediabucket": "evidence-bucket",
        "mediaextension": ".png"
    }

    mockDbConnection.execute = AsyncMock(return_value="DELETE 1")
    mockDbConnection.fetchrow = AsyncMock(return_value=mockMediaData)

    mockStorageClient = MagicMock()
    mockGetObject.return_value = mockStorageClient

    case = Case(CaseCreator="New_Dev", CaseName="The Jones v Smith")
    case.CaseId = uuid.uuid4()
    test_media_id = uuid.uuid4()
    
    result = await case.deleteEvidence(media_id=test_media_id)

    mockStorageClient.delete_object.assert_called_once_with(
        Bucket="evidence-bucket",
        Key="admin-mocked-uuid.png"
    )
    assert result["Status"] == "success"

@pytest.mark.asyncio
async def test_deleteEvidence_missing_case_id_400():
    """
    A missing Media_id should raise an exception
    """
    case = Case(CaseCreator="New_Dev", CaseName="The Jones v Smith")
    case.CaseId = None

    test_media_id = uuid.uuid4()
    test_user = "Investigator_Bob"

    with pytest.raises(HTTPException) as excInfo:
        await case.deleteEvidence(media_id=test_media_id, JWT_username=test_user)

    assert excInfo.value.status_code == 400
    assert excInfo.value.detail == "Case id is missing"

@pytest.mark.asyncio
@patch("asyncpg.connect")
async def test_deleteEvidence_investigator_unauthorized_403(mockDbConnect):
    """
An investigator tries to delete evidence but it fails due to either CaseCreator validation or record is missing (returns DELETE 0). Should raise 403.
    """
    mockDbConnection = AsyncMock()
    mockDbConnect.return_value = mockDbConnection

    mockDbConnection.execute = AsyncMock(return_value="DELETE 0")
    
    case = Case(CaseCreator="New_Dev", CaseName="The Jones v Smith")
    case.CaseId = uuid.uuid4()
    test_media_id = uuid.uuid4()
    test_user = "Hacker_Eve"

    with pytest.raises(HTTPException) as excInfo:
        await case.deleteEvidence(media_id=test_media_id, JWT_username=test_user)

    assert excInfo.value.status_code == 403
    assert "Unauthorized" in excInfo.value.detail


@pytest.mark.asyncio
@patch("asyncpg.connect")
async def test_deleteEvidence_admin_not_found_404(mockDbConnect):
    """
When an admin tries to delete a record that does not exist. (returns DELETE 0). Should raise 404.
    """
    mockDbConnection = AsyncMock()
    mockDbConnect.return_value = mockDbConnection

    mockDbConnection.execute = AsyncMock(return_value="DELETE 0")
    
    case = Case(CaseCreator="New_Dev", CaseName="The Jones v Smith")
    case.CaseId = uuid.uuid4()
    test_media_id = uuid.uuid4()

    with pytest.raises(HTTPException) as excInfo:
        await case.deleteEvidence(media_id=test_media_id)

    assert excInfo.value.status_code == 404
    assert excInfo.value.detail == "Media not found."

@pytest.mark.asyncio
async def tes_addEvidence_invalid_case_id_uuid():
    fileContent = b"A fake binary for a png"
    testContent = io.BytesIO(fileContent)

    mockMedia = UploadFile(
        file=testContent,
        filename="we_are_cooked.png",
        headers={"content-type": "image/png"}
    )

    case = Case(CaseCreator="New_Dev", CaseName="The Reciepts exposed")

    with pytest.raises(HTTPException) as excInfo:
        await case.addEvidence(media=mockMedia, case_id="not-a-valid-uuid")

    assert excInfo.value.status_code == 400
    assert excInfo.value.detail == "Invalid case_id UUID"

@pytest.mark.asyncio
@patch("app.core.cases.PdfReader")
async def test_addEvidence_pdf_open_action_rejected(mockPdfReaderClass):
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

    case = Case(CaseCreator="New_Dev", CaseName="The Reciepts exposed")
    test_case_id = uuid.uuid4()

    with pytest.raises(HTTPException) as excInfo:
        await case.addEvidence(media=mockMedia, case_id=test_case_id)

    assert excInfo.value.status_code == 400
    assert "security concern" in excInfo.value.detail

@pytest.mark.asyncio
@patch("app.core.cases.PdfReader")
async def test_addEvidence_pdf_javascript_rejected(mockPdfReaderClass):
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

    case = Case(CaseCreator="New_Dev", CaseName="The Reciepts exposed")
    test_case_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await case.addEvidence(media=mockMedia, case_id=test_case_id)

    assert exc_info.value.status_code == 400
    assert "security concern" in exc_info.value.detail
    
@pytest.mark.asyncio
@patch("asyncpg.connect")
@patch("app.core.cases.Minio")
@patch("app.core.cases.PdfReader")
@patch("uuid.uuid4")
async def test_addEvidence_pdf_javascript_rejected(mockUuid,mockPdfReaderClass, mockMinioClass, mockDbConnect):
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

    mockMinioClient = MagicMock()
    mockMinioClass.return_value = mockMinioClient
    

    case = Case(CaseCreator="New_Dev", CaseName="The Reciepts exposed")
    test_case_id = uuid.uuid4()

    result = await case.addEvidence(media=mockMedia, case_id=test_case_id)

    assert result is not None 
    assert "url" in result
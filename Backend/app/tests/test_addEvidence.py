import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException
import io
import uuid

from app.core.cases import Case
from starlette.datastructures import UploadFile


@pytest.mark.asyncio
@patch("asyncpg.connect")
@patch("app.core.cases.Minio")
@patch("uuid.uuid4")
async def test_images_upload_success(mockUuid, mockMinioClass, mockDbConnect):
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

    mockMinioClient = MagicMock()
    mockMinioClass.return_value = mockMinioClient

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

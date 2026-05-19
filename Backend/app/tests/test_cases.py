import pytest
import io
from fastapi import UploadFile, HTTPException
from app.core.cases import Case
from unittest.mock import patch, AsyncMock, MagicMock


def test_CaseCreationWithValidData():
    """Test successful case creation with valid inputs"""
    case = Case(CaseCreator="New_Dev", CaseName="The Jones v Smith")
    
    assert case.CaseCreator =="New_Dev"
    assert case.CaseName == "The Jones v Smith"


def test_CaseCreationRequiresCreator():
    """Test that case creation fails without CaseCreator"""
    with pytest.raises(ValueError, match="CaseCreator is required"):
        Case(CaseName="Test Case")


def test_CaseCreationRequiresCaseName():
    """Test that case creation fails without CaseName"""
    with pytest.raises(ValueError, match="CaseName is required"):
        Case(CaseCreator="alice_dev")

def test_NameIsTooLong():
    """ The name is too long """
    with pytest.raises(ValueError, match="Name is too long"):
        Case(
            CaseName="Test Case",
            CaseCreator="Case_2026_Test_Name_With_Exactly_One_Hundred_Characters_Long_For_Database_Validation_Testing_Purposes_THAT_is_right"
        )

def test_NameIs100():
    """The name is 100 characters that still too long"""
    with pytest.raises(ValueError, match="Name is too long"):
        Case(
            CaseName="Test Case",
            CaseCreator="Case_2026_Test_Name_With_Exactly_One_Hundred_Characters_Long_For_Database_Validation_Testing_Purposes_0"
        )


def test_CaseNameAt99Characters():
    """Test case creation with CaseName at 99 characters"""
    caseName99 = "A" * 99
    case = Case(CaseCreator="alice_dev", CaseName=caseName99)
    
    assert len(case.CaseName) == 99
    assert case.CaseName == caseName99


def test_CaseNameAt254Characters():
    """Test case creation with CaseName at 254 characters (within 255 limit)"""
    caseName254 = "A" * 254
    case = Case(CaseCreator="alice_dev", CaseName=caseName254)
    
    assert len(case.CaseName) == 254
    assert case.CaseName == caseName254


def test_CaseNameAt255Characters():
    """Test case creation with CaseName at 255 characters (at database limit)"""
    caseName255 = "A" * 255
    case = Case(CaseCreator="alice_dev", CaseName=caseName255)
    
    assert len(case.CaseName) == 255
    assert case.CaseName == caseName255


def test_CaseNameAt256Characters():
    """Test case creation with CaseName at 256 characters (exceeds 255 limit)"""
    caseName256 = "A" * 256
    
    with pytest.raises(ValueError, match="CaseName must be 255 characters or less"):
        Case(CaseCreator="alice_dev", CaseName=caseName256)

@pytest.mark.asyncio
@patch("asyncpg.connect")
async def test_SaveCaseWithMock(mock_connect):
    case = Case(CaseCreator="alice_dev", CaseName="Test Case")

    fakeDbUuid = "12345678-abcd-ef01-2345-6789abcdef01"

    # Mocking the database Connection therefore no actual database hit
    mockConnection = AsyncMock()
    mock_connect.return_value = mockConnection
    mockConnection.close = AsyncMock(return_value=None)

    mockConnection.fetchval = AsyncMock(return_value=fakeDbUuid)

    uuid = await case.save()

    assert uuid == fakeDbUuid
    assert isinstance(uuid, str)

    # Ensuring functions were called
    mock_connect.assert_called_once()
    mockConnection.fetchval.assert_called_once()
    mockConnection.close.assert_called_once()


#Testing for the media upload will start from here
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
        fileName = "success.png",
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

    mockDbConnection.fetchval = AsyncMock(return_value="mocked-evidence-uuid-123")
    mockDbConnection.close = AsyncMock()

    mockMinioClient = MagicMock()
    mockMinioClass.return_value = mockMinioClient

    case = Case(CaseCreator="New_Dev", CaseName="The Jones v Smith")

    result = await case.addEvidence(media=mockMedia)

    # Strict checks on the insert of that database

    firstCallArgs = mockDbConnection.fetchrow.call_args_list[0][0]
    lookupQuery = firstCallArgs[0]
    lookupParam = firstCallArgs[1]
    
    assert "FROM \"Cases_DB\".\"MediaType\"" in lookupQuery
    assert lookupParam == ".png"

    mockDbConnection.fetchval.assert_called_once()

    insertCallArgs = mockDbConnection.fetchval.call_args[0]
    sqlQuery = insertCallArgs[0]
    paramUuid = insertCallArgs[1]
    paramTypeId = insertCallArgs[2]
    paramHash = insertCallArgs[3]  

    assert "INSERT INTO \"Cases_DB\".\"Media\"" in sqlQuery
    assert "(\"mediaid\", \"mediatype\", \"mediahash\")" in sqlQuery

    assert paramUuid == fakeUuidString
    assert paramTypeId == "type-111" 
    assert len(paramHash) == 64

    expectedFilename = f"{fakeUuidString}.png"
    assert result["url"] == f"http://localhost:9000/images/{expectedFilename}"

    mockDbConnection.close.assert_called_once()

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

    with pytest.raises(HTTPException) as excInfo:
        await case.addEvidence(media=mockMedia)

    assert excInfo.value.status_code == 400
    assert "Unsupported file extension: .food" in excInfo.value.detail    

    mockDbConnection.close.assert_called_once()
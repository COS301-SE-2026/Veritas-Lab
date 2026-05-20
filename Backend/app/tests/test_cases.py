import pytest
import io
from fastapi import UploadFile, HTTPException
from app.core.cases import Case
from unittest.mock import patch, AsyncMock, MagicMock

def test_CaseCreationWithValidData():
    """Test successful case creation with valid inputs"""
    case = Case(CaseCreator="James Bond", CaseName="Flood in Durban")
    
    assert case.CaseCreator == "James Bond"
    assert case.CaseName == "Flood in Durban"
    assert case.CaseId is None
    assert case.CaseCreationDate is None
    assert case.CaseClosed is False

def test_CaseCreationRequiresCreator():
    """Test that case creation fails without CaseCreator"""
    with pytest.raises(ValueError, match="CaseCreator is required"):
        Case(CaseName="Test Case")

def test_CaseCreationRequiresCaseName():
    """Test that case creation fails without CaseName"""
    with pytest.raises(ValueError, match="CaseName is required"):
        Case(CaseCreator="alice_dev")

def test_CaseCreationRejectsBlankCreator():
    """Test that whitespace-only CaseCreator is rejected"""
    with pytest.raises(ValueError, match="CaseCreator is required"):
        Case(CaseCreator="   ", CaseName="Test Case")

def test_CaseCreationRejectsBlankCaseName():
    """Test that whitespace-only CaseName is rejected"""
    with pytest.raises(ValueError, match="CaseName is required"):
        Case(CaseCreator="alice_dev", CaseName="   ")

def test_NameIsTooLong():
    """Test that CaseCreator longer than 100 characters is rejected"""
    with pytest.raises(ValueError, match="Name is too long"):
        Case(
            CaseName="Test Case",
            CaseCreator="A" * 101
        )

def test_NameAt100Characters():
    """Test that CaseCreator at exactly 100 characters is accepted"""
    creator_name_100 = "A" * 100

    case = Case(
        CaseName="Test Case",
        CaseCreator=creator_name_100
    )

    assert len(case.CaseCreator) == 100
    assert case.CaseCreator == creator_name_100

def test_CaseNameAt99Characters():
    """Test case creation with CaseName at 99 characters"""
    caseName99 = "A" * 99
    case = Case(CaseCreator="alice_dev", CaseName=caseName99)
    
    assert len(case.CaseName) == 99
    assert case.CaseName == caseName99

def test_CaseNameAt254Characters():
    """Test case creation with CaseName at 254 characters"""
    case_name_254 = "A" * 254
    case = Case(CaseCreator="alice_dev", CaseName=case_name_254)
    
    assert len(case.CaseName) == 254
    assert case.CaseName == caseName254

def test_CaseNameAt255Characters():
    """Test case creation with CaseName at 255 characters"""
    case_name_255 = "A" * 255
    case = Case(CaseCreator="alice_dev", CaseName=case_name_255)
    
    assert len(case.CaseName) == 255
    assert case.CaseName == caseName255

def test_CaseNameAt256Characters():
    """Test case creation with CaseName at 256 characters is rejected"""
    case_name_256 = "A" * 256
    
    with pytest.raises(ValueError, match="CaseName must be 255 characters or less"):
        Case(CaseCreator="alice_dev", CaseName=caseName256)

def test_CaseStoresDescription():
    """Test that CaseDescription is stored correctly"""
    case = Case(
        CaseCreator="alice_dev",
        CaseName="Test Case",
        CaseDescription="This is a test description"
    )

    assert case.CaseDescription == "This is a test description"

def test_CaseStoresReviews():
    """Test that CaseReviews is stored correctly"""
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

@pytest.mark.asyncio
@patch("asyncpg.connect")
async def test_CreateCaseWithMock(mock_connect):
    """Test successful database insert using mocked asyncpg connection"""
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

    mock_connect.assert_called_once()
    mock_connection.fetchrow.assert_called_once()
    mock_connection.close.assert_called_once()

    assert excInfo.value.status_code == 400
    assert "Unsupported file extension: .food" in excInfo.value.detail    

@pytest.mark.asyncio
@patch("asyncpg.connect")
async def test_CreateCaseCannotBeCalledTwice(mock_connect):
    """Test that create() rejects a case that already has a CaseId"""
    case = Case(CaseCreator="alice_dev", CaseName="Test Case")
    case.CaseId = "12345678-abcd-ef01-2345-6789abcdef01"

    with pytest.raises(ValueError, match="This case already exists"):
        await case.create()

    mock_connect.assert_not_called()

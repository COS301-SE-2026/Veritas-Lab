import pytest
from app.core.cases import Case
from unittest.mock import patch, AsyncMock

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
    case_name_99 = "A" * 99
    case = Case(CaseCreator="alice_dev", CaseName=case_name_99)
    
    assert len(case.CaseName) == 99
    assert case.CaseName == case_name_99


def test_CaseNameAt254Characters():
    """Test case creation with CaseName at 254 characters (within 255 limit)"""
    case_name_254 = "A" * 254
    case = Case(CaseCreator="alice_dev", CaseName=case_name_254)
    
    assert len(case.CaseName) == 254
    assert case.CaseName == case_name_254


def test_CaseNameAt255Characters():
    """Test case creation with CaseName at 255 characters (at database limit)"""
    case_name_255 = "A" * 255
    case = Case(CaseCreator="alice_dev", CaseName=case_name_255)
    
    assert len(case.CaseName) == 255
    assert case.CaseName == case_name_255


def test_CaseNameAt256Characters():
    """Test case creation with CaseName at 256 characters (exceeds 255 limit)"""
    case_name_256 = "A" * 256
    
    with pytest.raises(ValueError, match="CaseName must be 255 characters or less"):
        Case(CaseCreator="alice_dev", CaseName=case_name_256)

@patch("asyncpg.connect")
async def test_SaveCaseWithMock(mock_connect):
    case = Case(CaseCreator="alice_dev", CaseName="Test Case")

    fake_db_uuid = "12345678-abcd-ef01-2345-6789abcdef01"

    # Mocking the database Connection therefore no actual database hit
    mock_connection = AsyncMock()
    mock_connect.return_value = mock_connection
    mock_connection.close = AsyncMock(return_value=None)

    mock_connection.fetchval = AsyncMock(return_value=fake_db_uuid)

    uuid = await case.save()

    assert uuid == fake_db_uuid
    assert isinstance(uuid, str)

    # Ensuring functions were called
    mock_connect.assert_called_once()
    mock_connection.fetchval.assert_called_once()
    mock_connection.close.assert_called_once()



import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone

from app.api.main import app
from app.core.cases import Case
import app.api.routers.cases_router as cases_router


client = TestClient(app)


def test_CaseCreationWithValidData():
    case = Case(CaseCreator="James Bond", CaseName="Flood in Durban")
    
    assert case.CaseCreator == "James Bond"
    assert case.CaseName == "Flood in Durban"
    assert case.CaseId is None
    assert case.CaseCreationDate is None
    assert case.CaseClosed is False


def test_CaseCreationRequiresCreator():
    with pytest.raises(ValueError, match="CaseCreator is required"):
        Case(CaseName="Test Case")


def test_CaseCreationRequiresCaseName():
    with pytest.raises(ValueError, match="CaseName is required"):
        Case(CaseCreator="alice_dev")


def test_CaseCreationRejectsBlankCreator():
    with pytest.raises(ValueError, match="CaseCreator is required"):
        Case(CaseCreator="   ", CaseName="Test Case")


def test_CaseCreationRejectsBlankCaseName():
    with pytest.raises(ValueError, match="CaseName is required"):
        Case(CaseCreator="alice_dev", CaseName="   ")


def test_NameIsTooLong():
    with pytest.raises(ValueError, match="Name is too long"):
        Case(
            CaseName="Test Case",
            CaseCreator="A" * 101
        )


def test_NameAt100Characters():
    creator_name_100 = "A" * 100

    case = Case(
        CaseName="Test Case",
        CaseCreator=creator_name_100
    )

    assert len(case.CaseCreator) == 100
    assert case.CaseCreator == creator_name_100


def test_CaseNameAt99Characters():
    case_name_99 = "A" * 99
    case = Case(CaseCreator="alice_dev", CaseName=case_name_99)
    
    assert len(case.CaseName) == 99
    assert case.CaseName == case_name_99


def test_CaseNameAt254Characters():
    case_name_254 = "A" * 254
    case = Case(CaseCreator="alice_dev", CaseName=case_name_254)
    
    assert len(case.CaseName) == 254
    assert case.CaseName == case_name_254


def test_CaseNameAt255Characters():
    case_name_255 = "A" * 255
    case = Case(CaseCreator="alice_dev", CaseName=case_name_255)
    
    assert len(case.CaseName) == 255
    assert case.CaseName == case_name_255


def test_CaseNameAt256Characters():
    case_name_256 = "A" * 256
    
    with pytest.raises(ValueError, match="CaseName must be 255 characters or less"):
        Case(CaseCreator="alice_dev", CaseName=case_name_256)


def test_CaseStoresDescription():
    case = Case(
        CaseCreator="alice_dev",
        CaseName="Test Case",
        CaseDescription="This is a test description"
    )

    assert case.CaseDescription == "This is a test description"


def test_CaseStoresReviews():
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


def test_CaseToJSONBeforeCreate():
    case = Case(
        CaseCreator="alice_dev",
        CaseName="Test Case",
        CaseDescription="This is a test description",
        CaseReviews={"status": "pending"}
    )

    result = case.toJSON()

    assert result == {
        "case_id": None,
        "case_name": "Test Case",
        "case_creator": "alice_dev",
        "case_reviews": {"status": "pending"},
        "case_description": "This is a test description",
        "case_closed": False,
        "case_creation_date": None
    }


def test_CaseToJSONAfterCreateValuesSet():
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
        "case_id": "12345678-abcd-ef01-2345-6789abcdef01",
        "case_name": "Test Case",
        "case_creator": "alice_dev",
        "case_reviews": {"reviewer": "admin", "status": "approved"},
        "case_description": "This is a test description",
        "case_closed": True,
        "case_creation_date": "2026-05-20T19:43:02+00:00"
    }


def test_CaseToJSONWithNoDescriptionOrReviews():
    case = Case(
        CaseCreator="alice_dev",
        CaseName="Test Case"
    )

    assert case.toJSON() == {
        "case_id": None,
        "case_name": "Test Case",
        "case_creator": "alice_dev",
        "case_reviews": None,
        "case_description": None,
        "case_closed": False,
        "case_creation_date": None
    }


@pytest.mark.asyncio
@patch("asyncpg.connect")
async def test_CreateCaseWithMock(mock_connect):
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
async def test_CreateCaseCannotBeCalledTwice(mock_connect):
    case = Case(CaseCreator="alice_dev", CaseName="Test Case")
    case.CaseId = "12345678-abcd-ef01-2345-6789abcdef01"

    with pytest.raises(ValueError, match="This case already exists"):
        await case.create()

    mock_connect.assert_not_called()


def testGetCasesMissingJWT(monkeypatch):
    def mock_verifyJWT(authorization):
        raise ValueError("Missing Authorization header")

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post("/api/getCases", json={})

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Missing Authorization header"
    }


def testGetCasesInvalidJWT(monkeypatch):
    def mock_verifyJWT(authorization):
        raise ValueError("Invalid token")

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/getCases",
        json={},
        headers={"Authorization": "Bearer fake-token"}
    )

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Invalid token"
    }


def testGetCasesUserRoleReturns403(monkeypatch):
    def mock_verifyJWT(authorization):
        return {
            "sub": "mock-user-id",
            "username": "normal_user",
            "role": "USER"
        }

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/getCases",
        json={},
        headers={"Authorization": "Bearer fake-token"}
    )

    assert response.status_code == 403
    assert response.json() == {
        "status": "error",
        "message": "User unauthorized"
    }


def testGetCasesAdminReturnsCases(monkeypatch):
    def mock_verifyJWT(authorization):
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
        json={},
        headers={"Authorization": "Bearer fake-token"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"
    assert len(data["cases"]) == 2

    assert data["cases"][0] == {
        "case_id": "12345678-abcd-ef01-2345-6789abcdef01",
        "case_name": "Flood in Durban",
        "case_creator": "admin_user",
        "case_reviews": None,
        "case_description": "Flood investigation case",
        "case_closed": False,
        "case_creation_date": "2026-05-20T19:43:02+00:00"
    }

    assert data["cases"][1] == {
        "case_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "case_name": "Fake Evidence Case",
        "case_creator": "investigator_user",
        "case_reviews": {"status": "pending"},
        "case_description": "Media verification case",
        "case_closed": False,
        "case_creation_date": "2026-05-21T10:30:00+00:00"
    }

    mock_connect.assert_called_once()
    mock_connection.fetch.assert_called_once()
    mock_connection.close.assert_called_once()


def testGetCasesInvestigatorReturnsEmptyList(monkeypatch):
    def mock_verifyJWT(authorization):
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
        json={},
        headers={"Authorization": "Bearer fake-token"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "cases": []
    }

    mock_connect.assert_called_once()
    mock_connection.fetch.assert_called_once()
    mock_connection.close.assert_called_once()

def testGetSingleCaseMissingJWT(monkeypatch):
    def mock_verifyJWT(authorization):
        raise ValueError("Missing Authorization header")

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post("/api/getSingleCase", json={})

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Missing Authorization header"
    }


def testGetSingleCaseInvalidJWT(monkeypatch):
    def mock_verifyJWT(authorization):
        raise ValueError("Invalid token")

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/getSingleCase",
        json={"CaseID": "12345678-abcd-ef01-2345-6789abcdef01"},
        headers={"Authorization": "Bearer fake-token"}
    )

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Invalid token"
    }


def testGetSingleCaseUserRoleReturns403(monkeypatch):
    def mock_verifyJWT(authorization):
        return {
            "sub": "mock-user-id",
            "username": "normal_user",
            "role": "USER"
        }

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/getSingleCase",
        json={"CaseID": "12345678-abcd-ef01-2345-6789abcdef01"},
        headers={"Authorization": "Bearer fake-token"}
    )

    assert response.status_code == 403
    assert response.json() == {
        "status": "error",
        "message": "User unauthorized"
    }


def testGetSingleCaseMissingCaseID(monkeypatch):
    def mock_verifyJWT(authorization):
        return {
            "sub": "mock-admin-id",
            "username": "admin_user",
            "role": "ADMIN"
        }

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/getSingleCase",
        json={},
        headers={"Authorization": "Bearer fake-token"}
    )

    assert response.status_code == 400
    assert response.json() == {
        "status": "error",
        "message": "CaseID required"
    }


def testGetSingleCaseInvalidCaseID(monkeypatch):
    def mock_verifyJWT(authorization):
        return {
            "sub": "mock-admin-id",
            "username": "admin_user",
            "role": "ADMIN"
        }

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/getSingleCase",
        json={"CaseID": "not-a-valid-uuid"},
        headers={"Authorization": "Bearer fake-token"}
    )

    assert response.status_code == 401
    assert response.json()["status"] == "error"


def testGetSingleCaseNotFound(monkeypatch):
    def mock_verifyJWT(authorization):
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
        json={"CaseID": "12345678-abcd-ef01-2345-6789abcdef01"},
        headers={"Authorization": "Bearer fake-token"}
    )

    assert response.status_code == 404
    assert response.json() == {
        "status": "error",
        "message": "Case not found"
    }

    mock_connect.assert_called_once()
    mock_connection.fetchrow.assert_called_once()
    mock_connection.close.assert_called_once()


def testGetSingleCaseAdminReturnsCase(monkeypatch):
    def mock_verifyJWT(authorization):
        return {
            "sub": "mock-admin-id",
            "username": "admin_user",
            "role": "ADMIN"
        }

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
        json={"CaseID": fake_case_id},
        headers={"Authorization": "Bearer fake-token"}
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "success",
        "case": {
            "case_id": fake_case_id,
            "case_name": "Flood in Durban",
            "case_creator": "admin_user",
            "case_reviews": {"status": "pending"},
            "case_description": "Flood investigation case",
            "case_closed": False,
            "case_creation_date": "2026-05-20T19:43:02+00:00"
        },
        "evidence": []
    }

    mock_connect.assert_called_once()
    mock_connection.fetchrow.assert_called_once()
    mock_connection.fetch.assert_called_once()
    mock_connection.close.assert_called_once()


def testGetSingleCaseReturnsLinkedEvidence(monkeypatch):
    def mock_verifyJWT(authorization):
        return {
            "sub": "mock-admin-id",
            "username": "admin_user",
            "role": "ADMIN"
        }

    fake_case_id = "12345678-abcd-ef01-2345-6789abcdef01"
    fake_report_id = "87654321-abcd-ef01-2345-6789abcdef01"
    fake_media_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    fake_case_row = {
        "caseid": fake_case_id,
        "casecreator": "admin_user",
        "casename": "Flood in Durban",
        "casereviews": {"status": "pending"},
        "casedescription": "Flood investigation case",
        "caseclosed": False,
        "casecreationdate": datetime(2026, 5, 20, 19, 43, 2, tzinfo=timezone.utc)
    }

    fake_evidence_rows = [
        {
            "reportid": fake_report_id,
            "caseid": fake_case_id,
            "mediaid": fake_media_id,
            "medianame": "123",
            "reportartifacts": {"ocr": "captured"},
            "reportfindings": "Flood watermark detected",
            "reportcomments": "Upload approved",
            "reportdatecreation": datetime(2026, 5, 21, 8, 15, 0, tzinfo=timezone.utc),
            "mediatypeid": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "mediabucket": "images",
            "mediaextension": ".png"
        }
    ]

    mock_connection = AsyncMock()
    mock_connection.fetchrow = AsyncMock(return_value=fake_case_row)
    mock_connection.fetch = AsyncMock(return_value=fake_evidence_rows)
    mock_connection.close = AsyncMock(return_value=None)

    mock_connect = AsyncMock(return_value=mock_connection)

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.asyncpg, "connect", mock_connect)

    response = client.post(
        "/api/getSingleCase",
        json={"CaseID": fake_case_id},
        headers={"Authorization": "Bearer fake-token"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "case": {
            "case_id": fake_case_id,
            "case_name": "Flood in Durban",
            "case_creator": "admin_user",
            "case_reviews": {"status": "pending"},
            "case_description": "Flood investigation case",
            "case_closed": False,
            "case_creation_date": "2026-05-20T19:43:02+00:00"
        },
        "evidence": [
            {
                "reportId": fake_report_id,
                "mediaId": fake_media_id,
                "mediaName": "123",
                "mediaBucket": "images",
                "mediaExtension": ".png",
                "mediaTypeId": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "mediaUrl": f"http://localhost:9000/images/{fake_media_id}.png",
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
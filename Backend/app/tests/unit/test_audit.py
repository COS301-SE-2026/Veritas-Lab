import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from datetime import datetime, timezone
from fastapi import HTTPException
import asyncpg

from app.api.main import app
import app.api.routers.cases_router as cases_router
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

#ste up local helpers
CASE_ID = "12345678-abcd-ef01-2345-6789abcdef01"

def _mock_jwt_success(monkeypatch, *, sub="mock-investigator-id", username="mock_investigator", role="INVESTIGATOR"):
    def mock_verify_jwt(request):
        return {"sub": sub, "username": username, "role": role}

    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        mock_verify_jwt
    )

def _mock_db_connect(monkeypatch, *, fetch_return=None):
    mock_connection = AsyncMock()
    mock_connection.fetch = AsyncMock(return_value=fetch_return)
    mock_connection.close = AsyncMock(return_value=None)
    mock_connect = AsyncMock(return_value=mock_connection)
    monkeypatch.setattr(
        cases_router.asyncpg,
        "connect", 
        mock_connect
    )
    return mock_connection, mock_connect

#Test Case 1 returns 200
def test_get_case_audit_events_success(monkeypatch):
    client.cookies.clear()
    _mock_jwt_success(monkeypatch)

    fake_rows = [
        {
            "eventtimestamp": datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc),
            "eventuser": "investigator_user",
            "eventaction": "Case Closed",
        },
        {
            "eventtimestamp": datetime(2024, 6, 2, 15, 30, tzinfo=timezone.utc),
            "eventuser": "admin_user",
            "eventaction": "Evidence Added",
        }
    ]

    mock_connection, mock_connect = _mock_db_connect(
        monkeypatch,
        fetch_return=fake_rows
    )

    response = client.get(f"/api/getAudit/caseID/{CASE_ID}")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"
    assert data["caseID"] == CASE_ID
    assert len(data["events"]) == 2

    assert data["events"][0] == {
        "timestamp": "2024-06-01T12:00:00+00:00",
        "user": "investigator_user",
        "action": "Case Closed"
    }

    mock_connect.assert_called_once()
    mock_connection.fetch.assert_called_once()
    mock_connection.close.assert_called_once()

def test_get_case_audit_events_user_unauthorized(monkeypatch):
    client.cookies.clear()
    _mock_jwt_success(monkeypatch,
    sub="mock-user-id",
    username="mock_user",
    role="USER" 
    )

    response = client.get(f"/api/getAudit/caseID/{CASE_ID}")

    assert response.status_code == 403
    data = response.json() == {
        "detail": {
            "status": "error",
            "message": cases_router.USER_UNAUTHORIZED
        }
    }

def test_get_case_audit_events_db_error(monkeypatch):
    client.cookies.clear()
    _mock_jwt_success(
        monkeypatch,
        sub="mock-admin-id",
        username="admin_user",
        role="ADMIN"
    )

    mock_connection, mock_connect = _mock_db_connect(monkeypatch)

    mock_connection.fetch.side_effect = asyncpg.PostgresError("Database error")

    response = client.get(f"/api/getAudit/caseID/{CASE_ID}")

    assert response.status_code == 500
    data = response.json() == {
        "detail": {
            "status": "error",
            "message": cases_router.DATABASE_ERROR_MESSAGE
        }
    }

#Testingh endpoint 2 for getting all audit logs for all cases

def test_get_audited_cases_success(monkeypatch):
    client.cookies.clear()
    _mock_jwt_success(
        monkeypatch,
        sub="mock-admin-id",
        username="admin_user",
        role="ADMIN"
    )

    fake_rows = [
        {
            "caseid": CASE_ID,
            "casename": "Flood in Westville",
            "eventcount": 5,
            "lasteventtimestamp": datetime(2024, 6, 2, 15, 30, tzinfo=timezone.utc),
            "caseexists": True
        },
        {
            "caseid": "87654321-dcba-10fe-5432-1098fedcba98",
            "casename": None,
            "eventcount": 3,
            "lasteventtimestamp": None,
            "caseexists": False
        }
    ]

    mock_connection, mock_connect = _mock_db_connect(
        monkeypatch,
        fetch_return=fake_rows
    )

    response = client.get("/api/getAllAudit")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"
    assert len(data["cases"]) == 2

    assert data["cases"][0] == {
        "caseId": CASE_ID,
        "caseName": "Flood in Westville",
        "eventCount": 5,
        "lastEventTimestamp": "2024-06-02T15:30:00+00:00",
        "caseExists": True
    }

    assert data["cases"][1]["caseName"] is None
    assert data["cases"][1]["lastEventTimestamp"] is None
    assert data["cases"][1]["caseExists"] is False

    mock_connect.assert_called_once()
    mock_connection.fetch.assert_called_once()
    mock_connection.close.assert_called_once()

def test_get_audited_cases_investigator_unauthorized(monkeypatch):
    client.cookies.clear()

    _mock_jwt_success(monkeypatch)

    response = client.get("/api/getAllAudit")

    assert response.status_code == 403
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": cases_router.USER_UNAUTHORIZED
        }
    }

def test_get_audited_cases_db_error(monkeypatch):
    client.cookies.clear()
    _mock_jwt_success(
        monkeypatch,
        sub="mock-admin-id",
        username="admin_user",
        role="ADMIN"
    )

    mock_connection, mock_connect = _mock_db_connect(monkeypatch)

    mock_connection.fetch.side_effect = asyncpg.PostgresError("Database error")

    response = client.get("/api/getAllAudit")

    assert response.status_code == 500
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": cases_router.DATABASE_ERROR_MESSAGE
        }
    }

def test_get_case_audit_events_empty_log(monkeypatch):
    client.cookies.clear()
    _mock_jwt_success(monkeypatch)

    mock_connection, mock_connect = _mock_db_connect(
        monkeypatch,
        fetch_return=[]
    )

    response = client.get(f"/api/getAudit/caseID/{CASE_ID}")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"
    assert data["caseID"] == CASE_ID
    assert len(data["events"]) == 0

    mock_connect.assert_called_once()
    mock_connection.fetch.assert_called_once()
    mock_connection.close.assert_called_once()

def test_get_audited_cases_empty_log(monkeypatch):
    client.cookies.clear()
    _mock_jwt_success(
        monkeypatch,
        sub="mock-admin-id",
        username="admin_user",
        role="ADMIN"
    )

    mock_connection, mock_connect = _mock_db_connect(
        monkeypatch,
        fetch_return=[]
    )

    response = client.get("/api/getAllAudit")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"
    assert len(data["cases"]) == 0

    mock_connect.assert_called_once()
    mock_connection.fetch.assert_called_once()
    mock_connection.close.assert_called_once()
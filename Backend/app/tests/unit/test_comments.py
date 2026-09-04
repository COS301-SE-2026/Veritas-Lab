"""
Integration tests for POST /api/cases/comments.
All DB and auth calls are mocked. No real db here.
"""

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from app.api.main import app
from app.auth.auth import COOKIE_NAME
import app.api.routers.cases_router as cases_router
from app.core.cases import Case
import pytest
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

VALID_CASE_ID = "12345678-abcd-ef01-2345-6789abcdef01"
VALID_COMMENT = "This is a valid comment."

FAKE_COMMENT_RESPONSE = {
    "commentId": 1,
    "caseId": VALID_CASE_ID,
    "username": "test_user",
    "comment": VALID_COMMENT,
    "timestamp": "2026-06-27T12:00:00",
}

INVESTIGATOR_JWT = {"userId": "user-1", "username": "investigator_one", "role": "INVESTIGATOR"}


def _jwt_mock(role="INVESTIGATOR", username="investigator_user"):
    return lambda req: {"sub": "id", "username": username, "role": role}


def _mock_connection():
    conn = AsyncMock()
    conn.close = AsyncMock(return_value=None)
    conn.transaction = MagicMock(return_value=AsyncMock())
    return conn


def _post_comment(body):
    return client.post(
        "/api/cases/comments",
        json=body,
        headers={"Authorization": "Bearer fake"},
    )


def _setup(
    monkeypatch, 
    role, 
    username, 
    *, 
    result=None, 
    exc=None
):
    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        _jwt_mock(role, username)
    )
    
    app.dependency_overrides[get_connection] = lambda: _mock_connection()
    monkeypatch.setattr(
        Case, 
        "add_comment", 
        AsyncMock(return_value=result, side_effect=exc)
    )


def _edit_comment_connection(return_data):
    async def _get_conn():
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value=None)
        mock_conn.fetchrow = AsyncMock(return_value=return_data)
        mock_conn.transaction = MagicMock(return_value=AsyncMock())
        return mock_conn
    return _get_conn


# Auth tests

def test_create_comment_missing_jwt(monkeypatch):
    client.cookies.clear()

    response = client.post("/api/cases/comments", 
        json={
            "case_id": VALID_CASE_ID, 
            "comment": VALID_COMMENT
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "status": "error", 
            "message": "Not authenticated"
        }
    }


def test_create_comment_invalid_jwt(monkeypatch):
    client.cookies.set(COOKIE_NAME, "invalid-token")

    response = _post_comment({"case_id": VALID_CASE_ID, "comment": VALID_COMMENT})

    assert response.status_code == 401
    assert response.json() == {
        "detail": {"status": "error", "message": "Invalid token"}
    }


# Input validation tests

def test_create_comment_missing_case_id(monkeypatch):
    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        _jwt_mock()
    )

    response = _post_comment({"comment": VALID_COMMENT})

    assert response.status_code == 422


def test_create_comment_invalid_case_id_format(monkeypatch):
    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        _jwt_mock()
    )

    response = _post_comment({"case_id": "not-a-uuid", "comment": VALID_COMMENT})

    assert response.status_code == 422


def test_create_comment_missing_comment(monkeypatch):
    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        _jwt_mock()
    )

    response = _post_comment({"case_id": VALID_CASE_ID})

    assert response.status_code == 400
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] == "Comment must be a non-empty string"


def test_create_comment_blank_comment(monkeypatch):
    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        _jwt_mock()
    )

    response = _post_comment({"case_id": VALID_CASE_ID, "comment": "   "})

    assert response.status_code == 400
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] == "Comment must be a non-empty string"


# Case existence and role-based access tests

def test_create_comment_case_not_found(monkeypatch):
    _setup(monkeypatch, "INVESTIGATOR", "investigator_user",
           exc=HTTPException(status_code=404, detail="Case not found"))

    response = _post_comment({"case_id": VALID_CASE_ID, "comment": VALID_COMMENT})

    assert response.status_code == 404
    assert response.json() == {"detail": "Case not found"}


def test_create_comment_user_on_open_case(monkeypatch):
    _setup(monkeypatch, "USER", "normal_user",
           exc=HTTPException(status_code=403, detail="Users may only comment on closed cases"))

    response = _post_comment({"case_id": VALID_CASE_ID, "comment": VALID_COMMENT})

    assert response.status_code == 403
    assert response.json() == {"detail": "Users may only comment on closed cases"}


def test_create_comment_investigator_on_closed_case(monkeypatch):
    _setup(
        monkeypatch,
        "INVESTIGATOR", 
        "investigator_user",
        exc=HTTPException(
            status_code=403, 
            detail="Investigators may only comment on open cases"
        )
    )

    response = _post_comment({
        "case_id": VALID_CASE_ID, 
        "comment": VALID_COMMENT
    })

    assert response.status_code == 403
    assert response.json() == {"detail": "Investigators may only comment on open cases"}


# Success tests

def test_create_comment_user_on_closed_case(monkeypatch):
    _setup(
        monkeypatch, 
        "USER", 
        "normal_user",
        result={
            **FAKE_COMMENT_RESPONSE, 
            "username": "normal_user", 
            "comment": VALID_COMMENT
        }
    )

    response = _post_comment({"case_id": VALID_CASE_ID, "comment": VALID_COMMENT})

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["comment"]["username"] == "normal_user"
    assert data["comment"]["comment"] == VALID_COMMENT
    assert isinstance(data["comment"]["commentId"], int)


def test_create_comment_investigator_on_open_case(monkeypatch):
    _setup(
        monkeypatch, 
        "INVESTIGATOR", 
        "investigator_user",
        result={
            **FAKE_COMMENT_RESPONSE, 
            "username": "investigator_user", 
            "comment": VALID_COMMENT
        }
    )

    response = _post_comment({"case_id": VALID_CASE_ID, "comment": VALID_COMMENT})

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["comment"]["username"] == "investigator_user"
    assert isinstance(data["comment"]["commentId"], int)


def test_create_comment_admin(monkeypatch):
    _setup(
        monkeypatch, 
        "ADMIN", 
        "admin_user",
        result={
            **FAKE_COMMENT_RESPONSE, 
            "username": "admin_user"
        }
    )

    response = _post_comment({
        "case_id": VALID_CASE_ID, 
        "comment": VALID_COMMENT
    })

    assert response.status_code == 201
    assert response.json()["status"] == "success"


# Edit comment tests

def test_update_comment_success(monkeypatch):
    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        _jwt_mock()
    )
    app.dependency_overrides[get_connection] = _edit_comment_connection({"commentid": 7})

    response = client.post(
        "/api/editComment/case/11111111-1111-1111-1111-111111111111/comment/7",
        json={"comment": "Updated findings after verification"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Comment edit successfully."}


def test_update_comment_invalid_token_returns_401(monkeypatch):
    def mock_verify_jwt(_):
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
        "/api/editComment/case/11111111-1111-1111-1111-111111111111/comment/7",
        json={"comment": "Edited comment"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Invalid token"
        }
    }


def test_update_comment_invalid_case_id_returns_400(monkeypatch):
    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        lambda _: INVESTIGATOR_JWT
    )

    response = client.post(
        "/api/editComment/case/not-a-valid-uuid/comment/7",
        json={"comment": "Edited comment"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "status": "error", 
            "message": "'not-a-valid-uuid' is not a valid UUID format"
        }
    }


def test_update_comment_not_found_returns_404(monkeypatch):
    monkeypatch.setattr(
        cases_router, 
        "verify_jwt", 
        _jwt_mock()
    )
    app.dependency_overrides[get_connection] = _edit_comment_connection(None)

    response = client.post(
        "/api/editComment/case/11111111-1111-1111-1111-111111111111/comment/404",
        json={"comment": "Edited comment"},
    )

    assert response.status_code == 404
    assert response.json() == {
       "detail": {
           "status": "error",
           "message": "Case not found or user unauthorized."
       }
    }

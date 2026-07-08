"""
Integration tests for POST /api/cases/comments.
All DB and auth calls are mocked. No real db here.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from app.api.main import app
import app.api.routers.cases_router as cases_router
from app.core.cases import Case

client = TestClient(app)

VALID_CASE_ID = "12345678-abcd-ef01-2345-6789abcdef01"
VALID_COMMENT = "This is a valid comment."

FAKE_COMMENT_RESPONSE = {
    "commentId": 1,
    "caseId": VALID_CASE_ID,
    "username": "test_user",
    "comment": VALID_COMMENT,
    "timestamp": "2026-06-27T12:00:00"
}

# Fake DB rows returned by connection.fetchrow for the Cases table lookup
OPEN_CASE_ROW = {
    "casecreator": "creator_user",
    "casename": "Test Case",
    "casedescription": "A test case",
    "caseclosed": False
}

CLOSED_CASE_ROW = {
    "casecreator": "creator_user",
    "casename": "Test Case",
    "casedescription": "A test case",
    "caseclosed": True
}

def _mock_connection(row=None):
    conn = AsyncMock()
    conn.fetchrow = AsyncMock(return_value=row)
    conn.close = AsyncMock(return_value=None)
    return conn


# Auth tests

def test_create_comment_missing_jwt(monkeypatch):
    def mock_verifyJWT(req):
        raise Exception("Missing Authorization header")

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post("/api/cases/comments", json={})

    assert response.status_code == 401
    assert response.json() == {"status": "error", "message": "Missing Authorization header"}


def test_create_comment_invalid_jwt(monkeypatch):
    def mock_verifyJWT(req):
        raise ValueError("Invalid token")

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/cases/comments",
        json={"case_id": VALID_CASE_ID, "comment": VALID_COMMENT},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 401
    assert response.json() == {"status": "error", "message": "Invalid token"}


# Input validation tests

def test_create_comment_missing_case_id(monkeypatch):
    def mock_verifyJWT(req):
        return {"sub": "id", "username": "investigator_user", "role": "INVESTIGATOR"}

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/cases/comments",
        json={"comment": VALID_COMMENT},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 400
    assert response.json() == {"status": "error", "message": "case_id is needed."}


def test_create_comment_invalid_case_id_format(monkeypatch):
    def mock_verifyJWT(req):
        return {"sub": "id", "username": "investigator_user", "role": "INVESTIGATOR"}

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/cases/comments",
        json={"case_id": "not-a-uuid", "comment": VALID_COMMENT},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 400
    assert response.json() == {"status": "error", "message": "Invalid case_id format"}


def test_create_comment_missing_comment(monkeypatch):
    def mock_verifyJWT(req):
        return {"sub": "id", "username": "investigator_user", "role": "INVESTIGATOR"}

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/cases/comments",
        json={"case_id": VALID_CASE_ID},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 400
    assert response.json()["status"] == "error"


def test_create_comment_blank_comment(monkeypatch):
    def mock_verifyJWT(req):
        return {"sub": "id", "username": "investigator_user", "role": "INVESTIGATOR"}

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/cases/comments",
        json={"case_id": VALID_CASE_ID, "comment": "   "},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 400
    assert response.json()["status"] == "error"


# Case existence and role-based access tests

def test_create_comment_case_not_found(monkeypatch):
    def mock_verifyJWT(req):
        return {"sub": "id", "username": "investigator_user", "role": "INVESTIGATOR"}

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router, "getConnection", AsyncMock(return_value=_mock_connection(row=None)))

    response = client.post(
        "/api/cases/comments",
        json={"case_id": VALID_CASE_ID, "comment": VALID_COMMENT},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 404
    assert response.json() == {"status": "error", "message": "Case not found"}


def test_create_comment_user_on_open_case(monkeypatch):
    def mock_verifyJWT(req):
        return {"sub": "id", "username": "normal_user", "role": "USER"}

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router, "getConnection", AsyncMock(return_value=_mock_connection(row=OPEN_CASE_ROW)))

    response = client.post(
        "/api/cases/comments",
        json={"case_id": VALID_CASE_ID, "comment": VALID_COMMENT},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 403
    assert response.json() == {"status": "error", "message": "Users may only comment on closed cases"}


def test_create_comment_investigator_on_closed_case(monkeypatch):
    def mock_verifyJWT(req):
        return {"sub": "id", "username": "investigator_user", "role": "INVESTIGATOR"}

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router, "getConnection", AsyncMock(return_value=_mock_connection(row=CLOSED_CASE_ROW)))

    response = client.post(
        "/api/cases/comments",
        json={"case_id": VALID_CASE_ID, "comment": VALID_COMMENT},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 403
    assert response.json() == {"status": "error", "message": "Investigators may only comment on open cases"}


# Success tests

def test_create_comment_user_on_closed_case(monkeypatch):
    """A USER commenting on a closed case should succeed with 201."""
    def mock_verifyJWT(req):
        return {"sub": "id", "username": "normal_user", "role": "USER"}

    async def mock_add_comment(self, connection, username, comment):
        return {**FAKE_COMMENT_RESPONSE, "username": username, "comment": comment}

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router, "getConnection", AsyncMock(return_value=_mock_connection(row=CLOSED_CASE_ROW)))
    monkeypatch.setattr(Case, "add_comment", mock_add_comment)

    response = client.post(
        "/api/cases/comments",
        json={"case_id": VALID_CASE_ID, "comment": VALID_COMMENT},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["comment"]["username"] == "normal_user"
    assert data["comment"]["comment"] == VALID_COMMENT
    assert isinstance(data["comment"]["commentId"], int)


def test_create_comment_investigator_on_open_case(monkeypatch):
    """An INVESTIGATOR commenting on an open case should succeed with 201."""
    def mock_verifyJWT(req):
        return {"sub": "id", "username": "investigator_user", "role": "INVESTIGATOR"}

    async def mock_add_comment(self, connection, username, comment):
        return {**FAKE_COMMENT_RESPONSE, "username": username, "comment": comment}

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router, "getConnection", AsyncMock(return_value=_mock_connection(row=OPEN_CASE_ROW)))
    monkeypatch.setattr(Case, "add_comment", mock_add_comment)

    response = client.post(
        "/api/cases/comments",
        json={"case_id": VALID_CASE_ID, "comment": VALID_COMMENT},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["comment"]["username"] == "investigator_user"
    assert isinstance(data["comment"]["commentId"], int)


def test_create_comment_admin_on_open_case(monkeypatch):
    """An ADMIN can comment on an open case."""
    def mock_verifyJWT(req):
        return {"sub": "id", "username": "admin_user", "role": "ADMIN"}

    async def mock_add_comment(self, connection, username, comment):
        return {**FAKE_COMMENT_RESPONSE, "username": username}

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router, "getConnection", AsyncMock(return_value=_mock_connection(row=OPEN_CASE_ROW)))
    monkeypatch.setattr(Case, "add_comment", mock_add_comment)

    response = client.post(
        "/api/cases/comments",
        json={"case_id": VALID_CASE_ID, "comment": VALID_COMMENT},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 201
    assert response.json()["status"] == "success"


def test_create_comment_admin_on_closed_case(monkeypatch):
    """An ADMIN can also comment on a closed case."""
    def mock_verifyJWT(req):
        return {"sub": "id", "username": "admin_user", "role": "ADMIN"}

    async def mock_add_comment(self, connection, username, comment):
        return {**FAKE_COMMENT_RESPONSE, "username": username}

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router, "getConnection", AsyncMock(return_value=_mock_connection(row=CLOSED_CASE_ROW)))
    monkeypatch.setattr(Case, "add_comment", mock_add_comment)

    response = client.post(
        "/api/cases/comments",
        json={"case_id": VALID_CASE_ID, "comment": VALID_COMMENT},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 201
    assert response.json()["status"] == "success"


def test_update_comment_success(monkeypatch):
    class MockConnection:
        async def fetchrow(self, query, case_id, username, comment_text, comment_id):
            return {"commentid": comment_id}

        async def close(self):
            pass

    async def mock_connect(*args, **kwargs):
        return MockConnection()

    def mock_verify_jwt(_authorization):
        return {
            "userId": "user-1",
            "username": "investigator_one",
            "role": "INVESTIGATOR"
        }

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verify_jwt)
    monkeypatch.setattr(cases_router.asyncpg, "connect", mock_connect)

    response = client.post(
        "/api/editComment/case/11111111-1111-1111-1111-111111111111/comment/7",
        json={"comment": "Updated findings after verification"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Comment edit successfully."
    }


def test_update_comment_invalid_token_returns_401(monkeypatch):
    def mock_verify_jwt(_authorization):
        raise ValueError("Invalid token")

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verify_jwt)

    response = client.post(
        "/api/editComment/case/11111111-1111-1111-1111-111111111111/comment/7",
        json={"comment": "Edited comment"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "Invalid token"
    }


def test_update_comment_invalid_case_id_returns_400(monkeypatch):
    def mock_verify_jwt(_authorization):
        return {
            "userId": "user-1",
            "username": "investigator_one",
            "role": "INVESTIGATOR"
        }

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verify_jwt)

    response = client.post(
        "/api/editComment/case/not-a-valid-uuid/comment/7",
        json={"comment": "Edited comment"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "status": "error",
        "message": "Invalid CaseID"
    }


def test_update_comment_not_found_returns_404(monkeypatch):
    class MockConnection:
        async def fetchrow(self, query, case_id, username, comment_text, comment_id):
            return None

        async def close(self):
            pass

    async def mock_connect(*args, **kwargs):
        return MockConnection()

    def mock_verify_jwt(_authorization):
        return {
            "userId": "user-1",
            "username": "investigator_one",
            "role": "INVESTIGATOR"
        }

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verify_jwt)
    monkeypatch.setattr(cases_router.asyncpg, "connect", mock_connect)

    response = client.post(
        "/api/editComment/case/11111111-1111-1111-1111-111111111111/comment/404",
        json={"comment": "Edited comment"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "status": "error",
        "message": "Case not found or user unauthorized."
    }

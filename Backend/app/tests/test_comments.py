"""
Integration tests for POST /api/cases/comments.
All DB and auth calls are mocked. No real db here.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from app.api.main import app
import app.api.routers.comments_router as comments_router

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

def _mock_connection():
    """Returns a mock asyncpg connection with a no-op close."""
    conn = AsyncMock()
    conn.close = AsyncMock(return_value=None)
    return conn

#Auth tests here.
#Verifying that the endpoint handles auth well.

def test_create_comment_missing_jwt(monkeypatch):
    def mock_verifyJWT(authorization):
        raise Exception("Missing Authorization header")

    monkeypatch.setattr(comments_router, "verifyJWT", mock_verifyJWT)

    response = client.post("/api/cases/comments", json={})

    assert response.status_code == 401
    assert response.json() == {"status": "error", "message": "Missing Authorization header"}

def test_create_comment_invalid_jwt(monkeypatch):
    def mock_verifyJWT(auth):
        raise ValueError("Invalid token")

    monkeypatch.setattr(comments_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/cases/comments",
        json={"case_id": VALID_CASE_ID, "comment": VALID_COMMENT},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 401
    assert response.json() == {"status": "error", "message": "Invalid token"}

#input validation tests

def test_create_comment_missing_case_id(monkeypatch):
    def mock_verifyJWT(auth):
        return {"sub": "id", "username": "investigator_user", "role": "INVESTIGATOR"}

    monkeypatch.setattr(comments_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/cases/comments",
        json={"comment": VALID_COMMENT},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 400
    assert response.json() == {"status": "error", "message": "case_id is needed."}

def test_create_comment_invalid_case_id_format(monkeypatch):
    def mock_verifyJWT(auth):
        return {"sub": "id", "username": "investigator_user", "role": "INVESTIGATOR"}

    monkeypatch.setattr(comments_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/cases/comments",
        json={"case_id": "not-a-uuid", "comment": VALID_COMMENT},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 400
    assert response.json() == {"status": "error", "message": "Invalid case_id format. Must be a valid UUID"}

def test_create_comment_missing_comment(monkeypatch):
    def mock_verifyJWT(auth):
        return {"sub": "id", "username": "investigator_user", "role": "INVESTIGATOR"}

    monkeypatch.setattr(comments_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/cases/comments",
        json={"case_id": VALID_CASE_ID},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 400
    assert response.json()["status"] == "error"

def test_create_comment_blank_comment(monkeypatch):
    def mock_verifyJWT(auth):
        return {"sub": "id", "username": "investigator_user", "role": "INVESTIGATOR"}

    monkeypatch.setattr(comments_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/cases/comments",
        json={"case_id": VALID_CASE_ID, "comment": "   "},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 400
    assert response.json()["status"] == "error"

def test_create_comment_too_long(monkeypatch):
    def mock_verifyJWT(auth):
        return {"sub": "id", "username": "investigator_user", "role": "INVESTIGATOR"}

    monkeypatch.setattr(comments_router, "verifyJWT", mock_verifyJWT)

    response = client.post(
        "/api/cases/comments",
        json={"case_id": VALID_CASE_ID, "comment": "A" * 2001},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 400
    assert response.json()["status"] == "error"

    #case status tests to be able to make a comment.

def test_create_comment_case_not_found(monkeypatch):
    def mock_verifyJWT(auth):
        return {"sub": "id", "username": "investigator_user", "role": "INVESTIGATOR"}

    async def mock_get_case_status(conn, case_id):
        return "not_found"

    monkeypatch.setattr(comments_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(comments_router, "get_case_status", mock_get_case_status)
    monkeypatch.setattr(comments_router.asyncpg, "connect", AsyncMock(return_value=_mock_connection()))

    response = client.post(
        "/api/cases/comments",
        json={"case_id": VALID_CASE_ID, "comment": VALID_COMMENT},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 404
    assert response.json() == {"status": "error", "message": "Case not found"}

def test_create_comment_user_on_open_case(monkeypatch):
    def mock_verifyJWT(auth):
        return {"sub": "id", "username": "normal_user", "role": "USER"}

    async def mock_get_case_status(conn, case_id):
        return "open"

    monkeypatch.setattr(comments_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(comments_router, "get_case_status", mock_get_case_status)
    monkeypatch.setattr(comments_router.asyncpg, "connect", AsyncMock(return_value=_mock_connection()))

    response = client.post(
        "/api/cases/comments",
        json={"case_id": VALID_CASE_ID, "comment": VALID_COMMENT},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 403
    assert response.json() == {"status": "error", "message": "Users may only comment on closed cases"}

def test_create_comment_investigator_on_closed_case(monkeypatch):
    """An INVESTIGATOR must not be able to comment on a case that is already closed."""
    def mock_verifyJWT(auth):
        return {"sub": "id", "username": "investigator_user", "role": "INVESTIGATOR"}

    async def mock_get_case_status(conn, case_id):
        return "closed"

    monkeypatch.setattr(comments_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(comments_router, "get_case_status", mock_get_case_status)
    monkeypatch.setattr(comments_router.asyncpg, "connect", AsyncMock(return_value=_mock_connection()))

    response = client.post(
        "/api/cases/comments",
        json={"case_id": VALID_CASE_ID, "comment": VALID_COMMENT},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 403
    assert response.json() == {"status": "error", "message": "Investigators may only comment on open cases"}

#Success tests
def test_create_comment_user_on_closed_case(monkeypatch):
    """A USER commenting on a closed case should succeed with 201."""
    def mock_verifyJWT(auth):
        return {"sub": "id", "username": "normal_user", "role": "USER"}

    async def mock_get_case_status(conn, case_id):
        return "closed"

    async def mock_insert_comment(conn, case_id, username, comment):
        return {**FAKE_COMMENT_RESPONSE, "username": username, "comment": comment}

    monkeypatch.setattr(comments_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(comments_router, "get_case_status", mock_get_case_status)
    monkeypatch.setattr(comments_router, "insert_comment", mock_insert_comment)
    monkeypatch.setattr(comments_router.asyncpg, "connect", AsyncMock(return_value=_mock_connection()))

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
    def mock_verifyJWT(auth):
        return {"sub": "id", "username": "investigator_user", "role": "INVESTIGATOR"}

    async def mock_get_case_status(conn, case_id):
        return "open"

    async def mock_insert_comment(conn, case_id, username, comment):
        return {**FAKE_COMMENT_RESPONSE, "username": username, "comment": comment}

    monkeypatch.setattr(comments_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(comments_router, "get_case_status", mock_get_case_status)
    monkeypatch.setattr(comments_router, "insert_comment", mock_insert_comment)
    monkeypatch.setattr(comments_router.asyncpg, "connect", AsyncMock(return_value=_mock_connection()))

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
    def mock_verifyJWT(auth):
        return {"sub": "id", "username": "admin_user", "role": "ADMIN"}

    async def mock_get_case_status(conn, case_id):
        return "open"

    async def mock_insert_comment(conn, case_id, username, comment):
        return {**FAKE_COMMENT_RESPONSE, "username": username}

    monkeypatch.setattr(comments_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(comments_router, "get_case_status", mock_get_case_status)
    monkeypatch.setattr(comments_router, "insert_comment", mock_insert_comment)
    monkeypatch.setattr(comments_router.asyncpg, "connect", AsyncMock(return_value=_mock_connection()))

    response = client.post(
        "/api/cases/comments",
        json={"case_id": VALID_CASE_ID, "comment": VALID_COMMENT},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 201
    assert response.json()["status"] == "success"


def test_create_comment_admin_on_closed_case(monkeypatch):
    """An ADMIN can also comment on a closed case."""
    def mock_verifyJWT(auth):
        return {"sub": "id", "username": "admin_user", "role": "ADMIN"}

    async def mock_get_case_status(conn, case_id):
        return "closed"

    async def mock_insert_comment(conn, case_id, username, comment):
        return {**FAKE_COMMENT_RESPONSE, "username": username}

    monkeypatch.setattr(comments_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(comments_router, "get_case_status", mock_get_case_status)
    monkeypatch.setattr(comments_router, "insert_comment", mock_insert_comment)
    monkeypatch.setattr(comments_router.asyncpg, "connect", AsyncMock(return_value=_mock_connection()))

    response = client.post(
        "/api/cases/comments",
        json={"case_id": VALID_CASE_ID, "comment": VALID_COMMENT},
        headers={"Authorization": "Bearer fake"}
    )

    assert response.status_code == 201
    assert response.json()["status"] == "success"

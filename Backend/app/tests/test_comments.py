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
    assert response.json() == {"status": "error", "message": "Invalid case_id format"}

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
from fastapi.testclient import TestClient
import pytest
from fastapi import Request
from unittest.mock import MagicMock
from app.api.main import app
from datetime import datetime, timedelta, timezone
import app.api.routers.cases_router as cases_router

client = TestClient(app)


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

def create_mock_request():
    """Helper to mock a robust FastAPI Request object for direct function testing"""
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/getComments",
        "headers": [(b"authorization", b"Bearer fake-token")],
        "app": MagicMock(),  # Prevents internal Starlette/FastAPI attribute crashes
        "query_string": b"",
        "path_params": {}
    }
    return Request(scope=scope)


@pytest.mark.asyncio
async def test_retrieve_comments_function_invalid_case_id(monkeypatch):
    def mock_verifyJWT(req):
        return {
            "sub": "mock-admin-id", 
            "username": "admin_user", 
            "role": "ADMIN"
        }
    
    class MockConnection:
        async def fetch(self, query, *args):
            return [
                {
                    "commentid": "99999999-9999-9999-9999-999999999999",
                    "commenttext": "Direct function test comment.",
                    "commentauthor": "admin_user",
                    "commentdate": datetime(2026, 6, 30, 2, 0, 0, tzinfo=timezone.utc)
                }
            ]

        async def close(self):
            pass

    async def mock_connect(*args, **kwargs):
        return MockConnection()

    monkeypatch.setattr(cases_router, "verifyJWT", mock_verifyJWT)
    monkeypatch.setattr(cases_router.asyncpg, "connect", mock_connect)

    mock_request = create_mock_request()

    response = await cases_router.retreive_comments(
        case_id="12345678-abcd-ef01-2345-6789abcdef01", 
        request=mock_request
    )

    assert response.status_code == 200
    
    import json
    response_data = json.loads(response.body.decode("utf-8"))
    
    assert response_data == {
        "status": "success",
        "comments": [{"commentauthor": "admin_user",'commentdate': '2026-06-30T02:00:00+00:00','commentid': '99999999-9999-9999-9999-999999999999',"commenttext": "Direct function test comment."}]
    }
from fastapi.testclient import TestClient

from app.api.main import app
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
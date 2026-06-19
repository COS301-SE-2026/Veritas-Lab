import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

#module that contains router, verufyJWT, deeleUserById
import app.auth.auth as auth

#Create a calid uuid for testing as the target to delete
TARGET_USER_ID = "11111111-1111-1111-1111-111111111111"
ADMNIN_USER_ID = "22222222-2222-2222-2222-222222222222"

@pytest.fixture
def client():
    """Builds a test client for the FastAPI app."""
    app = FastAPI()
    app.include_router(auth.router)
    return TestClient(app)

def admin_payload():
    return {"sub": ADMNIN_USER_ID, "username": "Admin", "role": "ADMIN"}

def test_admin_deletes_user_successfully(client, monkeypatch):

    monkeypatch.setattr(auth , "verifyJWT", lambda headers: admin_payload())

    async def fake_delete(user_id):
        return True #row found and deleted

    monkeypatch.setattr(auth, "deleteUsersById", fake_delete)

    response = client.delete(f"/api/users/{TARGET_USER_ID}", headers={"Authorization": "Bearer fakeToen"},)

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["message"] == "User deleted successfully."
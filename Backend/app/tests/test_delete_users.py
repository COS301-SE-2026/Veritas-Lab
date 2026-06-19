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

#Test for a logged in non-admin who tries to delete and gets blocked by 403 code error
def test_non_admin_is_forbiddedn(client, monkeypatch):

    monkeypatch.setattr(auth ,
        "verifyJWT", 
        lambda header: {"sub": ADMNIN_USER_ID, "username": "Alex", "role": "USER"})
        
    response = client.delete(f"/api/users/{TARGET_USER_ID}", headers={"Authorization": "Bearer fakeToken"},)
    
    assert response.status_code == 400
    assert response.json()["status"] == "error"

def test_missing_token_is_unauthorized(client, monkeypatch):

    """No or invalid token: verifyJWT rasises ValueError, the 401"""
    def raise_value_error(header):
        raise ValueError("Missing or invalid token")

    monkeypatch.setattr(auth, "verifyJWT", raise_value_error)

    response = client.delete(f"/api/users/{TARGET_USER_ID}")

    assert response.status_code == 401
    assert response.json()["status"] == "error"

def test_malformed_uuid_is_rejected(client, monkeypatch):

    monkeypatch.setattr(auth , "verifyJWT", lambda headers: admin_payload())

    malformed_uuid = "not-a-valid-uuid"
    response = client.delete(f"/api/users/{malformed_uuid}", headers={"Authorization": "Bearer fakeToken"},)

    assert response.status_code == 400
    assert response.json()["status"] == "error"
    assert response.json()["message"] == "Invalid User ID format."

#Admin cannot delete themselves. Error on return is 400
def test_admin_cannot_delete_themself(client, monkeypatch):

    monkeypatch.setattr(auth, "verifyJWT", lambda header: admin_payload())

    #The target is the same as the admin's ID
    response = client.delete(f"/api/users/{ADMNIN_USER_ID}", headers={"Authorization": "Bearer fakeToken"},)
    assert response.status_code == 400
    assert response.json()["status"] == "error"
    assert response.json()["message"] == "Admins cannot delete themselves."

#Testing nonexistent user with error code 404 
def test_nonexistent_user_delete_404(client, monkeypatch):
    
    monkeypatch.setattr(auth, "verifyJWT", lambda header: admin_payload())

    async def fake_delete(user_id):
        return False # found no one 

    monkeypatch.setattr(auth, "deleteUsersById", fake_delete)

    response = client.delete(
        f"/api/users/{TARGET_USER_ID}",
        headers={"Authorization": "Bearer fakeToken"}
    )

    assert response.status_code == 404
    assert response.json()["status"] == "error"

#invalid jwt is rejected
def test_invalid_jwt_rejected(client, monkeypatch):
    
    def fake_verify_raises(headers):
        raise ValueError("Invalid token")

    monkeypatch.setattr(auth, "verifyJWT", fake_verify_raises)

    response = client.delete(
        f"/api/users/{TARGET_USER_ID}",
        headers={"Authorization": "Bearer badToken"}
    )

    assert response.status_code == 401
    assert response.json()["status"] == "error"
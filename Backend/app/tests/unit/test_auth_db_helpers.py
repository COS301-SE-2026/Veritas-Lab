import pytest
from unittest.mock import MagicMock, AsyncMock
from jose import jwt
import app.auth.auth as auth
from app.auth.auth import (validate_uuid, create_token, search_users_via_email, search_users_via_username, update_user_jwt_issued, update_user_jwt_issued_via_user, delete_user_by_id, insert_user,)

def mock_connection(monkeypatch, fetchrowResult=None, executeResult=None):
    connection = MagicMock()
    connection.fetchrow = AsyncMock(return_value=fetchrowResult)
    connection.execute = AsyncMock(return_value=executeResult)
    connection.close = AsyncMock()

    monkeypatch.setattr(
        auth, 
        "get_connection", 
        AsyncMock(return_value=connection)
    )

    return connection

def test_validate_uuid_rejects_non_string():
    assert validate_uuid(123) == False

def test_create_token_contains_expected_claims():
    user = {"id": "11111111-1111-1111-1111-111111111111", "username": "Oh_nana", "role": "ADMIN"}

    token = create_token(user)

    decoded_token = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    assert decoded_token["sub"] == user["id"]
    assert decoded_token["username"] == user["username"]
    assert decoded_token["role"] == user["role"]

@pytest.mark.asyncio
async def test_search_users_via_email_found(monkeypatch):
    row = {
        "userid": "11111111-1111-1111-1111-111111111111",
        "useremail": "oh_nana@example.com",
        "username": "Oh_nana",
        "userrole" : "USER",
        "userpassword": "hashed_password",
    }
    connection = mock_connection(monkeypatch, fetchrowResult=row)

    result = await search_users_via_email("oh_nana@example.com", connection)

    assert result == {
        "id": row["userid"],
        "email": row["useremail"],
        "username": row["username"],
        "role": row["userrole"],
        "password": row["userpassword"]
    }
    connection.fetchrow.assert_awaited_once()
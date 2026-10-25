import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from app.api.main import app
from app.api.routers import cases_router
import app.auth.auth as auth
from datetime import datetime, timezone, timedelta
from app.core.database import get_connection
from app.tests.unit.database_override import unit_get_connection

COOKIE_NAME = auth.COOKIE_NAME
REFRESH_URL = "/api/refresh"
USER_ID = "12345678-abcd-ef01-2345-6789abcdef01"
TOKEN_LIFETIME_MINUTES = 10


@pytest.fixture(autouse=True)
def override_database_dependency():
    app.dependency_overrides[get_connection] = unit_get_connection
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_connection, None)

@pytest.fixture(autouse=True)
def fixed_token_lifetime(monkeypatch):
    monkeypatch.setattr(auth.auth_settings, "TOKEN_EXPIRE", TOKEN_LIFETIME_MINUTES)

def make_client(token: str | None = None) -> TestClient:
    """Create a TestClient with an optional cookie pre-set."""
    c = TestClient(app)
    if token is not None:
        c.cookies.set(COOKIE_NAME, token)
    return c

def stored_user(**overrides) -> dict:
    """The Users row that matches the default token claims."""
    row = {
        "userid": uuid.UUID(USER_ID),
        "username": "test_user",
        "userrole": "INVESTIGATOR",
        "userjwtissued": datetime.now(timezone.utc)
    }
    return {**row, **overrides}

def use_stored_user(monkeypatch, row: dict | None) -> MagicMock:
    """Make the handler's connection return row when it looks up the user."""
    mock_conn = MagicMock()
    mock_conn.fetchrow = AsyncMock(return_value=row)
    mock_conn.close = AsyncMock()
    monkeypatch.setattr(cases_router.asyncpg, "connect", AsyncMock(return_value=mock_conn))
    return mock_conn

def mock_decode_returning(monkeypatch, payload: dict):
    monkeypatch.setattr(auth.jwt, "decode", lambda *args, **kwargs: payload)

def token_payload(expires_in: timedelta, **overrides) -> dict:
    payload = {
        "sub": USER_ID,
        "username": "test_user",
        "role": "INVESTIGATOR",
        "exp": (datetime.now(timezone.utc) + expires_in).timestamp()
    }
    return {**payload, **overrides}

def assert_invalid_token(response):
    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Invalid token"
        }
    }
    assert auth.COOKIE_NAME not in response.cookies

def test_refresh_token_missing_cookie():
    response = make_client().post(REFRESH_URL)

    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Not authenticated"
        }
    }

def test_refresh_token_old_route_is_gone():
    response = make_client("valid-token").post("/api/refreshToken")

    assert response.status_code == 404

def test_refresh_token_invalid_jwt(monkeypatch):
    monkeypatch.setattr(
        auth.jwt,
        "decode",
        lambda *args,
        **kwargs: (_ for _ in ()).throw(auth.JWTError())
    )
    response = make_client("invalid-token").post(REFRESH_URL)

    assert_invalid_token(response)

def test_refresh_token_does_not_need_refreshing(monkeypatch):
    mock_decode_returning(monkeypatch, token_payload(timedelta(minutes=TOKEN_LIFETIME_MINUTES)))
    use_stored_user(monkeypatch, stored_user())

    response = make_client("valid-token").post(REFRESH_URL)

    assert response.status_code == 200
    assert response.json() == {
        "status":"success",
        "message":"Token does not need refreshing"
    }
    assert auth.COOKIE_NAME not in response.cookies

def test_refresh_token_success_within_one_minute(monkeypatch):
    expected_user = {
        "id": USER_ID,
        "username": "test_user",
        "role": "INVESTIGATOR"
    }

    def mock_create_token(user):
        assert user == expected_user
        return "new-mock-token"

    async def mock_update_user_jwt_issued_via_user(user, connection):
        assert user == expected_user

    mock_decode_returning(monkeypatch, token_payload(timedelta(seconds=30)))
    use_stored_user(monkeypatch, stored_user())
    monkeypatch.setattr(auth, "create_token", mock_create_token)
    monkeypatch.setattr(auth, "update_user_jwt_issued_via_user", mock_update_user_jwt_issued_via_user)

    response = make_client("almost-expired-token").post(REFRESH_URL)

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Token refreshed",
    }

    assert auth.COOKIE_NAME in response.cookies
    assert response.cookies.get(auth.COOKIE_NAME) == "new-mock-token"
    assert "SameSite=Lax" in response.headers["set-cookie"]

def test_refresh_token_success_when_expired(monkeypatch):
    decode_call_count = {"count": 0}

    def mock_jwt_decode(
        token,
        secret_key,
        algorithms,
        options=None
    ):
        decode_call_count["count"] += 1
        if decode_call_count["count"] == 1:
            raise auth.ExpiredSignatureError()
        return token_payload(timedelta(minutes=-1))

    def mock_create_token(user):
        assert user == {
            "id": USER_ID,
            "username": "test_user",
            "role": "INVESTIGATOR"
        }
        return "new-token-from-expired-token"

    async def mock_update_user_jwt_issued_via_user(user, connection):
        assert user["id"] == USER_ID

    monkeypatch.setattr(auth.jwt, "decode", mock_jwt_decode)
    use_stored_user(monkeypatch, stored_user())
    monkeypatch.setattr(auth, "create_token", mock_create_token)
    monkeypatch.setattr(auth, "update_user_jwt_issued_via_user", mock_update_user_jwt_issued_via_user)

    response = make_client("expired-token").post(REFRESH_URL)

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Token refreshed",
    }
    assert decode_call_count["count"] == 2
    assert auth.COOKIE_NAME in response.cookies
    assert response.cookies.get(auth.COOKIE_NAME) == "new-token-from-expired-token"

def test_refresh_token_expired_but_invalid_on_second_decode(monkeypatch):
    decode_call_count = {"count": 0}

    def mock_jwt_decode(token, secret_key, algorithms, options=None):
        decode_call_count["count"] += 1
        if decode_call_count["count"] == 1:
            raise auth.ExpiredSignatureError()
        raise auth.JWTError()

    monkeypatch.setattr(auth.jwt, "decode", mock_jwt_decode)

    response = make_client("expired-but-invalid-token").post(REFRESH_URL)

    assert_invalid_token(response)
    assert decode_call_count["count"] == 2

def test_refresh_token_missing_expiry(monkeypatch):
    payload = token_payload(timedelta(seconds=30))
    payload.pop("exp")
    mock_decode_returning(monkeypatch, payload)

    response = make_client("token-missing-expiry").post(REFRESH_URL)

    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Token missing expiry"
        }
    }
    assert auth.COOKIE_NAME not in response.cookies

def test_refresh_token_missing_required_fields(monkeypatch):
    mock_decode_returning(monkeypatch, {
        "sub": USER_ID,
        "exp": (datetime.now(timezone.utc) + timedelta(seconds=30)).timestamp()
    })

    response = make_client("token-missing-fields").post(REFRESH_URL)

    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Token missing required fields"
        }
    }
    assert auth.COOKIE_NAME not in response.cookies

def test_refresh_token_update_jwt_issued_fails(monkeypatch):
    async def mock_update_user_jwt_issued_via_user(user, connection):
        raise Exception("Database error")

    mock_decode_returning(monkeypatch, token_payload(timedelta(seconds=30)))
    use_stored_user(monkeypatch, stored_user())
    monkeypatch.setattr(auth, "create_token", lambda user: "new-mock-token")
    monkeypatch.setattr(auth, "update_user_jwt_issued_via_user", mock_update_user_jwt_issued_via_user)

    response = make_client("almost-expired-token").post(REFRESH_URL)

    assert response.status_code == 500
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Failed to update token issue time"
        }
    }
    assert auth.COOKIE_NAME not in response.cookies

# The claims in the token must match the database before a new token is issued

def test_refresh_token_role_changed_in_db(monkeypatch):
    mock_decode_returning(monkeypatch, token_payload(timedelta(seconds=30)))
    use_stored_user(monkeypatch, stored_user(userrole="USER"))
    create_token = MagicMock()
    monkeypatch.setattr(auth, "create_token", create_token)

    response = make_client("stale-role-token").post(REFRESH_URL)

    assert_invalid_token(response)
    create_token.assert_not_called()

def test_refresh_token_username_changed_in_db(monkeypatch):
    mock_decode_returning(monkeypatch, token_payload(timedelta(seconds=30)))
    use_stored_user(monkeypatch, stored_user(username="renamed_user"))

    response = make_client("stale-username-token").post(REFRESH_URL)

    assert_invalid_token(response)

def test_refresh_token_user_deleted(monkeypatch):
    mock_decode_returning(monkeypatch, token_payload(timedelta(seconds=30)))
    use_stored_user(monkeypatch, None)

    response = make_client("deleted-user-token").post(REFRESH_URL)

    assert_invalid_token(response)

def test_refresh_token_invalid_sub_is_401_not_500(monkeypatch):
    mock_decode_returning(monkeypatch, token_payload(timedelta(seconds=30), sub="not-a-uuid"))
    mock_conn = use_stored_user(monkeypatch, stored_user())

    response = make_client("bad-sub-token").post(REFRESH_URL)

    assert_invalid_token(response)
    mock_conn.fetchrow.assert_not_called()

def test_refresh_token_revoked_by_newer_login(monkeypatch):
    # The token was issued a lifetime minus 30s ago, but the user logged in again a minute ago
    mock_decode_returning(monkeypatch, token_payload(timedelta(seconds=30)))
    use_stored_user(monkeypatch, stored_user(userjwtissued=datetime.now(timezone.utc) - timedelta(minutes=1)))
    update_issued = AsyncMock()
    monkeypatch.setattr(auth, "update_user_jwt_issued_via_user", update_issued)

    response = make_client("revoked-token").post(REFRESH_URL)

    assert_invalid_token(response)
    update_issued.assert_not_called()

def test_refresh_token_revoked_even_when_no_refresh_needed(monkeypatch):
    # A revoked token must not get a 200 just because it is not close to expiry
    mock_decode_returning(monkeypatch, token_payload(timedelta(minutes=TOKEN_LIFETIME_MINUTES - 2)))
    use_stored_user(monkeypatch, stored_user(userjwtissued=datetime.now(timezone.utc) - timedelta(minutes=1)))

    response = make_client("revoked-fresh-token").post(REFRESH_URL)

    assert_invalid_token(response)

def test_logout_missing_cookie():
    response = make_client().post("/api/logout")

    assert response.status_code == 401
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Not authenticated"
        }
    }

def test_logout_invalid_jwt(monkeypatch):
    monkeypatch.setattr(
        auth.jwt,
        "decode",
        lambda *args, **kwargs: (_ for _ in ()).throw(auth.JWTError())
    )

    response = make_client("invalid-token").post("/api/logout")

    assert_invalid_token(response)

def test_logout_success(monkeypatch):
    payload = token_payload(timedelta(minutes=5))
    mock_decode_returning(monkeypatch, payload)
    use_stored_user(monkeypatch, stored_user())
    clear_session = AsyncMock()
    monkeypatch.setattr(auth, "clear_user_jwt_issued", clear_session)

    response = make_client("valid-token").post("/api/logout")

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Logged out successfully"
    }
    delete_cookie = response.headers["set-cookie"]
    assert delete_cookie.startswith(f"{COOKIE_NAME}=")
    assert "Max-Age=0" in delete_cookie
    assert "SameSite=Lax" in delete_cookie
    clear_session.assert_awaited_once()
    assert clear_session.await_args.args[0] == USER_ID

def test_logout_clear_session_failure(monkeypatch):
    mock_decode_returning(monkeypatch, token_payload(timedelta(minutes=5)))
    use_stored_user(monkeypatch, stored_user())
    monkeypatch.setattr(
        auth,
        "clear_user_jwt_issued",
        AsyncMock(side_effect=Exception("Database error"))
    )

    response = make_client("valid-token").post("/api/logout")

    assert response.status_code == 500
    assert response.json() == {
        "detail": {
            "status": "error",
            "message": "Failed to log out"
        }
    }

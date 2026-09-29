import asyncio
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import asyncpg
import httpx
import pytest
from dotenv import dotenv_values
from jose import jwt

ENV = dotenv_values(Path(__file__).resolve().parents[2] / ".env")
API = "http://localhost:8000/api"
SYSTEM_INIT_ID = "00000000-0000-0000-0000-000000000000"

BCRYPT_COST_12_PLUS = re.compile(r"^\$2[aby]\$(1[2-9]|[23]\d)\$.{53}$")  # e.g. $2b$12$ + 53 chars = 60
ANY_BCRYPT_HASH = re.compile(r"\$2[aby]\$\d\d\$")
SENSITIVE_NAME = re.compile(r"pass|token|secret|jwt|email", re.IGNORECASE)

# A fresh throwaway account per run, so the result never depends on existing data
RUN = uuid.uuid4().hex[:8]
EMAIL = f"qr07_{RUN}@example.com"
USERNAME = f"qr07_{RUN}"
PASSWORD = f"Qr07-Old-{RUN}!1"
NEW_PASSWORD = f"Qr07-New-{RUN}!2"


def jwt_from(resp: httpx.Response) -> str:
    """Pulls the JWT_token value out of the Set-Cookie header."""
    match = re.search(r"JWT_token=([^;]+)", resp.headers.get("set-cookie", ""))
    assert match, f"no JWT_token cookie on {resp.request.url}"
    return match.group(1)


def as_cookie(token: str) -> dict:
    return {"Cookie": f"JWT_token={token}"}


def db_fetch(sql: str, *args):
    """Runs one read-only query directly against the compose Postgres."""
    async def run():
        conn = await asyncpg.connect(
            user=ENV["DB_USER"], password=ENV["DB_PASSWORD"], database=ENV["DB_NAME"],
            host="localhost", port=int(ENV.get("DB_PORT") or 5432),
        )
        try:
            return await conn.fetch(sql, *args)
        finally:
            await conn.close()
    return asyncio.run(run())


def near_expiry_token() -> str:
    """A validly signed token for the throwaway user that expires in 60 s.
    /refreshToken only re-issues a cookie in the last half of a token's lifespan, so this forces a real refresh."""
    user_id = db_fetch('SELECT userid::text FROM "Users_DB"."Users" WHERE username = $1', USERNAME)[0][0]
    payload = {"sub": user_id, "username": USERNAME, "role": "USER",
               "exp": datetime.now(timezone.utc) + timedelta(seconds=60)}
    return jwt.encode(payload, ENV["JWT_SECRET"], algorithm=ENV["HASH"])


def walk_keys(obj):
    """Yields every key name in a nested JSON body."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            yield from walk_keys(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from walk_keys(item)


@pytest.fixture(scope="module")
def session():
    """Registers the throwaway user, logs in as it and as the admin, and deletes it afterwards."""
    with httpx.Client(base_url=API, timeout=30) as client:
        register = client.post("/register", json={"email": EMAIL, "username": USERNAME, "password": PASSWORD})
        assert register.status_code == 201, register.text
        login = client.post("/login", json={"email": EMAIL, "password": PASSWORD})
        assert login.status_code == 200, login.text
        admin = client.post("/login", json={"email": ENV["ADMIN_EMAIL"], "password": ENV["ADMIN_PASSWORD"]})
        assert admin.status_code == 200, admin.text

        state = {"client": client, "register": register, "login": login, "admin_jwt": jwt_from(admin)}
        yield state

        # Clean-up: delete the throwaway user through the admin API
        users = client.post("/fetchUsers", headers=as_cookie(state["admin_jwt"])).json()["users"]
        user_id = next(u["id"] for u in users if u["username"] == USERNAME)
        client.delete(f"/users/{user_id}", headers=as_cookie(state["admin_jwt"]))


def test_a_every_stored_password_is_bcrypt_cost_12_or_more(session):
    rows = db_fetch('SELECT userid::text AS id, username, userpassword FROM "Users_DB"."Users"')
    users = [r for r in rows if r["id"] != SYSTEM_INIT_ID]
    weak = [r["username"] for r in users if not BCRYPT_COST_12_PLUS.match(r["userpassword"])]
    print(f"\n[QR-07a] {len(users) - len(weak)}/{len(users)} stored passwords are bcrypt with cost >= 12")
    assert weak == [], f"not bcrypt cost>=12: {weak}"

    ours = next(r for r in users if r["username"] == USERNAME)["userpassword"]
    assert PASSWORD not in ours, "plaintext password found in the stored value"


def test_b_no_response_exposes_a_password_or_hash(session):
    client = session["client"]
    responses = {
        "POST /register": session["register"],
        "POST /login": session["login"],
        "POST /fetchUsers (admin)": client.post("/fetchUsers", headers=as_cookie(session["admin_jwt"])),
    }
    refresh = client.post("/refreshToken", headers=as_cookie(near_expiry_token()))
    assert refresh.json()["message"] == "Token refreshed", refresh.text
    responses["POST /refreshToken"] = session["refresh"] = refresh

    old_hash = db_fetch('SELECT userpassword FROM "Users_DB"."Users" WHERE username = $1', USERNAME)[0][0]
    responses["POST /changePassword"] = client.post(
        "/changePassword", headers=as_cookie(jwt_from(refresh)),
        json={"currentPassword": PASSWORD, "newPassword": NEW_PASSWORD})

    for name, resp in responses.items():
        assert resp.status_code < 300, f"{name} -> {resp.status_code} {resp.text}"
        assert not ANY_BCRYPT_HASH.search(resp.text), f"{name} leaks a bcrypt hash"
        leaked = [k for k in walk_keys(resp.json()) if "password" in k.lower()]
        assert leaked == [], f"{name} returns password fields {leaked}"
    print(f"\n[QR-07b] 0 of {len(responses)} responses expose a password or hash: {', '.join(responses)}")

    new_hash = db_fetch('SELECT userpassword FROM "Users_DB"."Users" WHERE username = $1', USERNAME)[0][0]
    assert BCRYPT_COST_12_PLUS.match(new_hash) and new_hash != old_hash


def test_c_no_credentials_or_tokens_in_urls():
    spec = httpx.get(f"{API}/openapi.json", timeout=30).json()
    url_params = set()
    for path, operations in spec["paths"].items():
        url_params.update(re.findall(r"{(\w+)}", path))  # path parameters
        for op in operations.values():
            if isinstance(op, dict):
                url_params.update(p["name"] for p in op.get("parameters", []) if p["in"] in ("path", "query"))
    print(f"\n[QR-07c] {len(spec['paths'])} routes checked, URL parameters found: {sorted(url_params)}")
    assert [p for p in url_params if SENSITIVE_NAME.search(p)] == []


def test_d_jwt_cookie_is_httponly_and_secure(session):
    for name in ("register", "login", "refresh"):  # 'refresh' is set by test_b, so run the whole file
        cookie = session[name].headers["set-cookie"]
        print(f"\n[QR-07d] {name}: {re.sub(r'JWT_token=[^;]+', 'JWT_token=<redacted>', cookie)}")
        assert re.search(r";\s*HttpOnly\b", cookie, re.I), f"{name} cookie is not HttpOnly"
        assert re.search(r";\s*Secure\b", cookie, re.I), f"{name} cookie is not Secure"
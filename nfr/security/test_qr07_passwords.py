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

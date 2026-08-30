import uuid
import asyncpg
import pytest
import pytest_asyncio
from app.core.env import Postgres_Settings
from fastapi.testclient import TestClient
from app.api.main import app

POSTGRES_SETTINGS = Postgres_Settings()

async def get_connection() -> asyncpg.Connection:
    conn = await asyncpg.connect(
        user=POSTGRES_SETTINGS.DB_USER,
        password=POSTGRES_SETTINGS.DB_PASSWORD,
        database=POSTGRES_SETTINGS.DB_NAME,
        host=POSTGRES_SETTINGS.DB_HOST,
        port=POSTGRES_SETTINGS.DB_PORT,
        ssl="require" if POSTGRES_SETTINGS.DB_SSL else None,
    )
    return conn

@pytest_asyncio.fixture
async def ensure_user_exists():
    created_users = []

    async def _ensure_user(
        conn: asyncpg.Connection, 
        user_id: str, 
        username: str, 
        role: str = "INVESTIGATOR"
    ):
        unique_username = f"{username}_{user_id[:8]}"
        unique_email = f"{unique_username}@audit-test.local"
        
        await conn.execute(f"SET app.current_user_id = '{user_id}';")

        await conn.execute(
            '''
            INSERT INTO "Users_DB"."Users" (UserId, UserEmail, UserName, UserRole, UserPassword)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (UserId) DO NOTHING
            ''',
            uuid.UUID(user_id),
            unique_email,
            unique_username,
            role,
            "audit-test-password"
        )
        created_users.append(user_id)

    yield _ensure_user

    if created_users:
        cleanup_conn = await get_connection()
        try:
            for user_id in created_users:
                await cleanup_conn.execute(
                    'DELETE FROM "Users_DB"."Users" WHERE UserId = $1',
                    uuid.UUID(user_id)
                )

            await cleanup_conn.execute(
                'TRUNCATE TABLE "Cases_DB"."Audit_Cases"'
            )

            await cleanup_conn.execute(
                'TRUNCATE TABLE "Cases_DB"."Audit_Media"'
            )

            await cleanup_conn.execute(
                'TRUNCATE TABLE "Cases_DB"."Audit_MediaTypes"'
            )

            await cleanup_conn.execute(
                'TRUNCATE TABLE "Cases_DB"."Audit_Comments"'
            )
            
        finally:
            await cleanup_conn.close()

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
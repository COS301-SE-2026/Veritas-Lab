import uuid
import asyncpg
import pytest
import pytest_asyncio
from app.core.env import Postgres_Settings
from fastapi.testclient import TestClient
from app.api.main import app
from app.auth.auth import create_token


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

        await conn.execute("SELECT set_config('app.current_user_id', $1, false)", user_id)

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

@pytest_asyncio.fixture
async def case_assignment_context(ensure_user_exists):
    conn = await get_connection()

    investigator_id = str(uuid.uuid4())
    admin_id = str(uuid.uuid4())
    other_investigator_id = str(uuid.uuid4())
    creator_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    investigator = f"Test_Investigator_{investigator_id[:8]}"
    admin = f"Test_Admin_{admin_id[:8]}"
    other_investigator = f"Other_Investigator_{other_investigator_id[:8]}"
    creator = f"Test_Creator_{creator_id[:8]}"
    user = f"Test_User_{user_id[:8]}"

    await ensure_user_exists(
        conn,
        investigator_id,
        investigator,
        "INVESTIGATOR"
    )

    await ensure_user_exists(
        conn,
        admin_id,
        admin,
        "ADMIN"
    )

    await ensure_user_exists(
        conn,
        other_investigator_id,
        other_investigator,
        "INVESTIGATOR"
    )

    await ensure_user_exists(
        conn,
        creator_id,
        creator,
        "USER"
    )

    await ensure_user_exists(
        conn,
        user_id,
        user,
        "USER"
    )

    created_case_ids = []

    try:
        yield {
            "conn": conn,

            "investigator_id": investigator_id,
            "investigator_name": investigator,
            "investigator_token": create_token(
                {
                    "id": investigator_id,
                    "username": investigator,
                    "role": "INVESTIGATOR"
                }
            ),

            "admin_id": admin_id,
            "admin_name": admin,
            "admin_token": create_token(
                {
                    "id": admin_id,
                    "username": admin,
                    "role": "ADMIN"
                }
            ),

            "other_investigator_id": other_investigator_id,
            "other_investigator_name": other_investigator,

            "creator_id": creator_id,
            "creator_name": creator,

            "user_id": user_id,
            "user_name": user,
            "user_token": create_token(
                {
                    "id": user_id,
                    "username": user,
                    "role": "USER"
                }
            ),

            "cases": created_case_ids,
        }

    finally:
        await conn.execute(
            "SELECT set_config('app.current_user_id', $1, false)",
            investigator_id
        )

        for case_id in created_case_ids:
            await conn.execute(
                """
                DELETE FROM "Cases_DB"."Cases"
                WHERE caseid = $1
                """,
                uuid.UUID(case_id)
            )

        await conn.close()
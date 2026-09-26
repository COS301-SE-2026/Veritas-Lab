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

        return unique_username

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

    # verify_jwt checks token usernames against the database, so use the usernames that were actually stored
    investigator = await ensure_user_exists(
        conn,
        investigator_id,
        "Test_Investigator",
        "INVESTIGATOR"
    )

    admin = await ensure_user_exists(
        conn,
        admin_id,
        "Test_Admin",
        "ADMIN"
    )

    other_investigator = await ensure_user_exists(
        conn,
        other_investigator_id,
        "Other_Investigator",
        "INVESTIGATOR"
    )

    creator = await ensure_user_exists(
        conn,
        creator_id,
        "Test_Creator",
        "USER"
    )

    user = await ensure_user_exists(
        conn,
        user_id,
        "Test_User",
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

async def get_automated_annotations(media_id):
    connection = await get_connection()

    try:
        return await connection.fetchrow(
            """
            SELECT
                AnnotationId,
                MediaId,
                MediaAnnotations,
                CreatedAt
            FROM "Cases_DB"."AutomatedAnnotations"
            WHERE MediaId = $1
            """,
            media_id
        )

    finally:
        await connection.close()

@pytest_asyncio.fixture
async def pnp_case_context(case_assignment_context):
    context = case_assignment_context
    conn = context["conn"]

    media_type_id = uuid.uuid4()
    media_id = uuid.uuid4()
    case_id = uuid.uuid4()

    await conn.execute(
        """
        SELECT set_config('app.current_user_id', $1, false)
        """,
        context["investigator_id"]
    )

    await conn.execute(
        """
        INSERT INTO "Cases_DB"."MediaType"
            (MediaTypeId, MediaName, MediaBucket, MediaExtension)
        VALUES
            ($1, $2, $3, $4)
        """,
        media_type_id,
        f"PNP_Test_Type_{str(media_type_id)[:8]}",
        "pnp-test-bucket",
        f".{str(media_type_id)[:4]}"
    )

    await conn.execute(
        """
        INSERT INTO "Cases_DB"."Media"
            (MediaId, MediaType, MediaHash, MediaAnnotations)
        VALUES
            ($1, $2, $3, $4::jsonb)
        """,
        media_id,
        media_type_id,
        f"pnp-test-hash-{media_id}",
        "{}"
    )

    # CaseAssigned must be NULL when the case is first created.
    await conn.execute(
        """
        INSERT INTO "Cases_DB"."Cases"
            (
                CaseId,
                CaseName,
                CaseCreator,
                CaseDescription,
                CaseState,
                evidence
            )
        VALUES
            (
                $1,
                $2,
                $3,
                $4,
                'PUBLISHED',
                ARRAY[
                    ROW($5::uuid, $6::text)::"Cases_DB".evidence_type
                ]
            )
        """,
        case_id,
        "PNP Integration Test Case",
        context["creator_name"],
        "Case used for PNP integration testing",
        media_id,
        "Test evidence"
    )

    # Assign the case only after creation.
    await conn.execute(
        """
        UPDATE "Cases_DB"."Cases"
        SET CaseAssigned = $1
        WHERE CaseId = $2
        """,
        context["investigator_name"],
        case_id
    )

    context["cases"].append(str(case_id))

    try:
        yield {
            **context,
            "case_id": case_id,
            "media_id": media_id,
            "media_type_id": media_type_id
        }

    finally:
        await conn.execute(
            """
            SELECT set_config('app.current_user_id', $1, false)
            """,
            context["investigator_id"]
        )

        await conn.execute(
            """
            DELETE FROM "Cases_DB"."PNPModels"
            WHERE MediaId = $1
            """,
            media_id
        )

        # The case contains this media in its evidence array, but there is no FK
        # from evidence to Media, so deleting Media before the Case is acceptable.
        await conn.execute(
            """
            DELETE FROM "Cases_DB"."Media"
            WHERE MediaId = $1
            """,
            media_id
        )

        await conn.execute(
            """
            DELETE FROM "Cases_DB"."MediaType"
            WHERE MediaTypeId = $1
            """,
            media_type_id
        )
import uuid

import pytest
import pytest_asyncio

from fastapi.testclient import TestClient

from app.api.main import app
from app.auth.auth import COOKIE_NAME, create_token
from app.core.cases import get_object
from app.core.env import Postgres_Settings
from app.core.media_relay import MediaRelay
from app.tests.integration.conftest import get_connection

POSTGRES_SETTINGS = Postgres_Settings()

CASE_CREATOR = "TestUploadInvestigator"
OTHER_INVESTIGATOR = "SomeoneElse"
EVIDENCE_BUCKET = "images"
EVIDENCE_EXTENSION = ".png"


@pytest.fixture(autouse=True)
def stub_media_pipeline(monkeypatch):
    async def no_op(self):
        return None

    monkeypatch.setattr(MediaRelay, "relay_to_service", no_op)


def cookie_for(username: str, role: str, user_id: str | None = None) -> str:
    return create_token(
        {
            "id": user_id or str(uuid.uuid4()),
            "username": username,
            "role": role,
        }
    )


def png_bytes(marker: str) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + marker.encode()


async def insert_case(conn, case_id, creator, closed, user_id):
    await conn.execute("SELECT set_config('app.current_user_id', $1, false)", user_id)
    await conn.execute(
        """
        INSERT INTO "Cases_DB"."Cases"
        (CaseId, CaseName, CaseCreator, CaseDescription, CaseClosed)
        VALUES ($1, $2, $3, $4, $5)
        """,
        uuid.UUID(case_id),
        f"Upload evidence test case {case_id[:8]}",
        creator,
        "Integration test case for evidence upload",
        closed,
    )


@pytest_asyncio.fixture
async def fake_upload_context(ensure_user_exists):
    conn = await get_connection()
    created_ids = {}

    try:
        creator_user_id = str(uuid.uuid4())
        other_user_id = str(uuid.uuid4())
        open_case_id = str(uuid.uuid4())
        other_case_id = str(uuid.uuid4())
        closed_case_id = str(uuid.uuid4())

        created_ids.update(
            {
                "open_case_id": open_case_id,
                "other_case_id": other_case_id,
                "closed_case_id": closed_case_id,
                "creator_user_id": creator_user_id,
                "other_user_id": other_user_id,
            }
        )

        await ensure_user_exists(conn, creator_user_id, CASE_CREATOR, "INVESTIGATOR")
        await ensure_user_exists(conn, other_user_id, OTHER_INVESTIGATOR, "INVESTIGATOR")

        await conn.execute("SELECT set_config('app.current_user_id', $1, false)", creator_user_id)

        await conn.execute(
            """
            INSERT INTO "Cases_DB"."Cases"
            (CaseId, CaseName, CaseCreator, CaseDescription, CaseClosed)
            VALUES ($1, $2, $3, $4, $5)
            """,
            uuid.UUID(open_case_id),
            f"Upload evidence test case {open_case_id[:8]}",
            CASE_CREATOR,
            "Integration test case for evidence upload",
            False,
        )

        await conn.execute(
            """
            INSERT INTO "Cases_DB"."Cases"
            (CaseId, CaseName, CaseCreator, CaseDescription, CaseClosed)
            VALUES ($1, $2, $3, $4, $5)
            """,
            uuid.UUID(other_case_id),
            f"Upload evidence test case {other_case_id[:8]}",
            OTHER_INVESTIGATOR,
            "Integration test case for evidence upload",
            False,
        )

        await conn.execute(
            """
            INSERT INTO "Cases_DB"."Cases"
            (CaseId, CaseName, CaseCreator, CaseDescription, CaseClosed)
            VALUES ($1, $2, $3, $4, $5)
            """,
            uuid.UUID(closed_case_id),
            f"Upload evidence test case {closed_case_id[:8]}",
            CASE_CREATOR,
            "Integration test case for evidence upload",
            True,
        )

        await conn.execute(
            """
            INSERT INTO "Cases_DB"."MediaType" (MediaTypeId, MediaBucket, MediaExtension, MediaName)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (MediaExtension) DO NOTHING
            """,
            uuid.uuid4(),
            "evidence-bucket",
            "png",
            "PNG Image",
        )

        yield {
            "open_case_id": open_case_id,
            "other_case_id": other_case_id,
            "closed_case_id": closed_case_id,
            "creator_user_id": creator_user_id,
            "other_user_id": other_user_id,
        }

    finally:
        created_case_ids = [
            uuid.UUID(created_ids["open_case_id"]),
            uuid.UUID(created_ids["other_case_id"]),
            uuid.UUID(created_ids["closed_case_id"]),
        ]

        media_ids = []
        await conn.execute("SELECT set_config('app.current_user_id', $1, false)", created_ids["creator_user_id"])
        for case_id in created_case_ids:
            rows = await conn.fetch(
                'SELECT mediaid FROM "Cases_DB"."Reports" WHERE caseid = $1',
                case_id,
            )
            media_ids.extend(str(row["mediaid"]) for row in rows)

            await conn.execute(
                'DELETE FROM "Cases_DB"."Cases" WHERE caseid = $1',
                case_id,
            )

        for media_id in media_ids:
            await conn.execute(
                'DELETE FROM "Cases_DB"."Media" WHERE mediaid = $1',
                uuid.UUID(media_id),
            )

        await conn.execute(
            'DELETE FROM "Users_DB"."Users" WHERE userid = ANY($1::uuid[])',
            [
                uuid.UUID(created_ids["creator_user_id"]),
                uuid.UUID(created_ids["other_user_id"]),
            ],
        )

        storage_client = get_object()
        for media_id in media_ids:
            try:
                storage_client.delete_object(
                    Bucket=EVIDENCE_BUCKET,
                    Key=f"{media_id}{EVIDENCE_EXTENSION}",
                )
            except Exception:
                pass

        await conn.close()


def upload(client, case_id, content, filename="evidence.png"):
    return client.post(
        "/api/cases/evidence",
        data={"case_id": case_id},
        files={"media": (filename, content, "image/png")},
    )


@pytest.mark.asyncio
async def test_integration_upload_evidence_success(client, fake_upload_context):
    client.cookies.set(
        COOKIE_NAME,
        cookie_for(CASE_CREATOR, "INVESTIGATOR", fake_upload_context["creator_user_id"]),
    )

    response = upload(
        client,
        fake_upload_context["open_case_id"],
        png_bytes("success"),
    )

    assert response.status_code == 201
    data = response.json()

    assert data["status"] == "success"
    assert data["evidence"]["Status"] == "uploaded"

    media_id = data["evidence"]["MediaId"]

    conn = await get_connection()
    try:
        media_row = await conn.fetchrow(
            'SELECT MediaId FROM "Cases_DB"."Media" WHERE MediaId = $1',
            uuid.UUID(media_id),
        )
        report_row = await conn.fetchrow(
            'SELECT ReportId FROM "Cases_DB"."Reports" WHERE MediaId = $1',
            uuid.UUID(media_id),
        )
    finally:
        await conn.close()

    assert media_row is not None
    assert report_row is not None

    storage_client = get_object()
    head = storage_client.head_object(
        Bucket=EVIDENCE_BUCKET,
        Key=f"{media_id}{EVIDENCE_EXTENSION}",
    )
    assert head["ContentLength"] > 0


@pytest.mark.asyncio
async def test_integration_upload_evidence_duplicate_returns_409(client, fake_upload_context):
    client.cookies.set(
        COOKIE_NAME,
        cookie_for(CASE_CREATOR, "INVESTIGATOR", fake_upload_context["creator_user_id"]),
    )

    content = png_bytes("duplicate")
    case_id = fake_upload_context["open_case_id"]

    first = upload(client, case_id, content)
    assert first.status_code == 201

    second = upload(client, case_id, content)

    assert second.status_code == 409
    assert second.json()["detail"]["status"] == "error"


@pytest.mark.asyncio
async def test_integration_upload_evidence_user_forbidden(client, fake_upload_context):
    client.cookies.set(COOKIE_NAME, cookie_for("StandardUser", "USER"))

    response = upload(
        client,
        fake_upload_context["open_case_id"],
        png_bytes("forbidden"),
    )

    assert response.status_code == 403
    assert response.json()["detail"]["message"] == "User unauthorized"


@pytest.mark.asyncio
async def test_integration_upload_evidence_not_case_creator(client, fake_upload_context):
    client.cookies.set(
        COOKIE_NAME,
        cookie_for(CASE_CREATOR, "INVESTIGATOR", fake_upload_context["creator_user_id"]),
    )

    response = upload(
        client,
        fake_upload_context["other_case_id"],
        png_bytes("not-creator"),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_integration_upload_evidence_closed_case(client, fake_upload_context):
    client.cookies.set(
        COOKIE_NAME,
        cookie_for(CASE_CREATOR, "INVESTIGATOR", fake_upload_context["creator_user_id"]),
    )

    response = upload(
        client,
        fake_upload_context["closed_case_id"],
        png_bytes("closed"),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_integration_upload_evidence_malformed_case_id(client):
    client.cookies.set(
        COOKIE_NAME,
        cookie_for(CASE_CREATOR, "INVESTIGATOR", str(uuid.uuid4())),
    )

    response = upload(client, "not-a-valid-uuid", png_bytes("malformed"))

    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "'not-a-valid-uuid' is not a valid UUID format"


@pytest.mark.asyncio
async def test_integration_upload_evidence_unsupported_extension(client, fake_upload_context):
    client.cookies.set(
        COOKIE_NAME,
        cookie_for(CASE_CREATOR, "INVESTIGATOR", fake_upload_context["creator_user_id"]),
    )

    response = upload(
        client,
        fake_upload_context["open_case_id"],
        b"definitely not an image",
        filename="malware.exe",
    )

    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]["message"]


@pytest.mark.asyncio
async def test_integration_upload_evidence_unauthorized(client, fake_upload_context):
    client.cookies.clear()

    response = upload(
        client,
        fake_upload_context["open_case_id"],
        png_bytes("unauthorized"),
    )

    assert response.status_code == 401
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] == "Not authenticated"
import pytest
import pytest_asyncio
import uuid
import asyncpg
from fastapi.testclient import TestClient

from app.api.main import app
from app.auth.auth import COOKIE_NAME, create_token
from app.core.cases import get_object
from app.core.env import Postgres_Settings
from app.core.media_relay import MediaRelay

POSTGRES_SETTINGS = Postgres_Settings()

CASE_CREATOR = "TestUploadInvestigator"
OTHER_INVESTIGATOR = "SomeoneElse"
EVIDENCE_BUCKET = "images"
EVIDENCE_EXTENSION = ".png"


async def get_connection() -> asyncpg.Connection:
    return await asyncpg.connect(
        user=POSTGRES_SETTINGS.DB_USER,
        password=POSTGRES_SETTINGS.DB_PASSWORD,
        database=POSTGRES_SETTINGS.DB_NAME,
        host=POSTGRES_SETTINGS.DB_HOST,
        port=POSTGRES_SETTINGS.DB_PORT,
        ssl="require" if POSTGRES_SETTINGS.DB_SSL else None,
    )


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(autouse=True)
def stub_media_pipeline(monkeypatch):
    async def no_op(self):
        return None

    monkeypatch.setattr(MediaRelay,"relay_to_service", no_op)

def cookie_for(username: str, role: str) -> str:
    return create_token({
        "id": str(uuid.uuid4()),
        "username": username,
        "role": role,
    })


# add_evidence dedupes on a sha256 of the file bytes, so every upload that is meant to succeed needs its own content.
def png_bytes(marker: str) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + marker.encode()


async def insert_case(conn, case_id, creator, closed):
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
async def fake_upload_context():
    conn = await get_connection()
    created_ids = {}

    try:
        for key, creator, closed in (
            ("open_case_id", CASE_CREATOR, False),
            ("closed_case_id", CASE_CREATOR, True),
            ("other_case_id", OTHER_INVESTIGATOR, False),
        ):
            case_id = str(uuid.uuid4())
            await insert_case(conn, case_id, creator, closed)
            created_ids[key] = case_id

        yield created_ids

    finally:
        media_ids = []

        for key in ("open_case_id", "closed_case_id", "other_case_id"):
            if key not in created_ids:
                continue

            rows = await conn.fetch(
                'SELECT MediaId FROM "Cases_DB"."Reports" WHERE CaseId = $1',
                uuid.UUID(created_ids[key]),
            )
            media_ids.extend(str(row["mediaid"]) for row in rows)

            await conn.execute(
                'DELETE FROM "Cases_DB"."Cases" WHERE CaseId = $1',
                uuid.UUID(created_ids[key]),
            )

        for media_id in media_ids:
            await conn.execute(
                'DELETE FROM "Cases_DB"."Media" WHERE MediaId = $1',
                uuid.UUID(media_id),
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
    client.cookies.set(COOKIE_NAME, cookie_for(CASE_CREATOR, "INVESTIGATOR"))

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
    client.cookies.set(COOKIE_NAME, cookie_for(CASE_CREATOR, "INVESTIGATOR"))

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
    client.cookies.set(COOKIE_NAME, cookie_for(CASE_CREATOR, "INVESTIGATOR"))

    response = upload(
        client,
        fake_upload_context["other_case_id"],
        png_bytes("not-creator"),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_integration_upload_evidence_closed_case(client, fake_upload_context):
    client.cookies.set(COOKIE_NAME, cookie_for(CASE_CREATOR, "INVESTIGATOR"))

    response = upload(
        client,
        fake_upload_context["closed_case_id"],
        png_bytes("closed"),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_integration_upload_evidence_malformed_case_id(client):
    client.cookies.set(COOKIE_NAME, cookie_for(CASE_CREATOR, "INVESTIGATOR"))

    response = upload(client, "not-a-valid-uuid", png_bytes("malformed"))

    assert response.status_code == 400
    assert response.json()["detail"]["status"] == "error"


@pytest.mark.asyncio
async def test_integration_upload_evidence_unsupported_extension(client, fake_upload_context):
    client.cookies.set(COOKIE_NAME, cookie_for(CASE_CREATOR, "INVESTIGATOR"))

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

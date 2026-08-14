import pytest
from fastapi.testclient import TestClient
from app.api.main import app
import pytest_asyncio
import uuid
from app.auth.auth import create_token, COOKIE_NAME
from app.tests.integration.test_int_annotations import get_connection, client
from app.core.cases import get_object
from botocore.exceptions import ClientError

@pytest_asyncio.fixture
async def fake_evidence_context():
    conn = await get_connection()
    s3_client = get_object()
    created_ids = {}

    try:
        media_type_row = await conn.fetchrow(
            """
            SELECT MediaTypeId, MediaBucket, MediaExtension 
            FROM "Cases_DB"."MediaType" 
            LIMIT 1;
            """
        )
        
        if not media_type_row:
            raise RuntimeError("No seeded MediaType found in database. Seed MediaType first.")

        media_type_id = media_type_row["mediatypeid"]
        media_bucket = media_type_row["mediabucket"]
        media_extension = media_type_row["mediaextension"] or ""

        case_id = str(uuid.uuid4())
        case_creator = "TestInvest"
        await conn.execute(
            """
            INSERT INTO "Cases_DB"."Cases" 
            (CaseId, CaseName, CaseCreator, CaseDescription, CaseClosed)
            VALUES ($1, $2, $3, $4, $5)
            """,
            uuid.UUID(case_id),
            "Delete Evidence Integration Test",
            case_creator,
            "Temporary case for testing evidence deletion",
            False
        )
        created_ids["case_id"] = case_id

        media_id = str(uuid.uuid4())
        media_hash = uuid.uuid4().hex
        await conn.execute(
            """
            INSERT INTO "Cases_DB"."Media" 
            (MediaId, MediaType, MediaHash)
            VALUES ($1, $2, $3)
            """,
            uuid.UUID(media_id),
            media_type_id,
            media_hash
        )
        created_ids["media_id"] = media_id

        report_row = await conn.fetchrow(
            """
            INSERT INTO "Cases_DB"."Reports" 
            (CaseId, MediaId, ImageTitle)
            VALUES ($1, $2, $3)
            RETURNING ReportId
            """,
            uuid.UUID(case_id),
            uuid.UUID(media_id),
            "Fake Evidence Title"
        )
        created_ids["report_id"] = str(report_row["reportid"])

        file_key = f"{media_id}{media_extension}"
        s3_client.put_object(
            Bucket=media_bucket,
            Key=file_key,
            Body=b"fake evidence file binary content for testing"
        )
        created_ids["file_key"] = file_key
        created_ids["bucket"] = media_bucket

        yield {
            "case_id": case_id,
            "media_id": media_id,
            "creator": case_creator,
            "bucket": media_bucket,
            "file_key": file_key
        }

    finally:

        if "file_key" in created_ids and "bucket" in created_ids:
            try:
                s3_client.delete_object(
                    Bucket=created_ids["bucket"],
                    Key=created_ids["file_key"]
                )
            except Exception:
                pass

        if "case_id" in created_ids:
            await conn.execute(
                'DELETE FROM "Cases_DB"."Cases" WHERE CaseId = $1',
                uuid.UUID(created_ids["case_id"])
            )

        if "media_id" in created_ids:
            await conn.execute(
                'DELETE FROM "Cases_DB"."Media" WHERE MediaId = $1',
                uuid.UUID(created_ids["media_id"])
            )

        await conn.close()


async def assert_object_storage_not_deleted(media_id,case_id,context):
    s3_client = get_object()
    s3_response = s3_client.get_object(
        Bucket=context["bucket"],
        Key=context["file_key"]
    )
    assert s3_response["ResponseMetadata"]["HTTPStatusCode"] == 200

    conn = await get_connection()
    try:
        report_row = await conn.fetchrow(
            'SELECT * FROM "Cases_DB"."Reports" WHERE CaseId = $1 AND MediaId = $2',
            uuid.UUID(case_id),
            uuid.UUID(media_id)
        )
        assert report_row is not None
    finally:
        await conn.close()


#403: Not the owner deleting
@pytest.mark.asyncio
async def test_integration_delete_evidence_403_not_creator(client, fake_evidence_context):
    case_id = fake_evidence_context["case_id"]
    media_id = fake_evidence_context["media_id"]

    unauthorized_investigator = {
        "id": str(uuid.uuid4()),
        "username": "UnauthorizedUser",
        "role": "INVESTIGATOR"
    }
    client.cookies.set(COOKIE_NAME, create_token(unauthorized_investigator))

    response = client.post(f"/api/delete/case/{case_id}/evidence/{media_id}")

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] =="Unauthorized to delete this evidence or record not found."
    await assert_object_storage_not_deleted(media_id,case_id,fake_evidence_context)
    
#403: USER deleting
@pytest.mark.asyncio
async def test_integration_delete_evidence_403_user(client, fake_evidence_context):
    case_id = fake_evidence_context["case_id"]
    media_id = fake_evidence_context["media_id"]

    unauthorized_investigator = {
        "id": str(uuid.uuid4()),
        "username": "UnauthorizedUser",
        "role": "USER"
    }
    client.cookies.set(COOKIE_NAME, create_token(unauthorized_investigator))

    response = client.post(f"/api/delete/case/{case_id}/evidence/{media_id}")

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] =="User unauthorized"
    await assert_object_storage_not_deleted(media_id,case_id,fake_evidence_context)


#400: invalid Case Id
@pytest.mark.asyncio
async def test_integration_delete_evidence_400_case_id(client, fake_evidence_context):
    case_id = "invalid case id"
    media_id = fake_evidence_context["media_id"]

    unauthorized_investigator = {
        "id": str(uuid.uuid4()),
        "username": "UnauthorizedUser",
        "role": "INVESTIGATOR"
    }
    client.cookies.set(COOKIE_NAME, create_token(unauthorized_investigator))

    response = client.post(f"/api/delete/case/{case_id}/evidence/{media_id}")

    assert response.status_code == 400
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] ==f"'{case_id}' is not a valid UUID format"
    await assert_object_storage_not_deleted(media_id,fake_evidence_context["case_id"],fake_evidence_context)


#200
@pytest.mark.asyncio
async def test_integration_delete_evidence_investigator_success(client, fake_evidence_context):
    case_id = fake_evidence_context["case_id"]
    media_id = fake_evidence_context["media_id"]
    creator = fake_evidence_context["creator"]

    mock_investigator = {
        "id": str(uuid.uuid4()),
        "username": creator,
        "role": "INVESTIGATOR"
    }
    client.cookies.set(COOKIE_NAME, create_token(mock_investigator))

    response = client.post(f"/api/delete/case/{case_id}/evidence/{media_id}")

    assert response.status_code == 200
    assert response.json()=={
        "status":"success",
        "deleted":media_id
    }


    s3_client = get_object()
    with pytest.raises(ClientError):
        s3_client.get_object(
            Bucket=fake_evidence_context["bucket"],
            Key=fake_evidence_context["file_key"]
        )

#200
@pytest.mark.asyncio
async def test_integration_delete_evidence_admin_success(client, fake_evidence_context):
    case_id = fake_evidence_context["case_id"]
    media_id = fake_evidence_context["media_id"]
    creator = "freckles"

    mock_investigator = {
        "id": str(uuid.uuid4()),
        "username": creator,
        "role": "ADMIN"
    }
    client.cookies.set(COOKIE_NAME, create_token(mock_investigator))

    response = client.post(f"/api/delete/case/{case_id}/evidence/{media_id}")

    assert response.status_code == 200
    assert response.json()=={
        "status":"success",
        "deleted":media_id
    }


    s3_client = get_object()
    with pytest.raises(ClientError):
        s3_client.get_object(
            Bucket=fake_evidence_context["bucket"],
            Key=fake_evidence_context["file_key"]
        )

#404: No media
@pytest.mark.asyncio
async def test_integration_delete_evidence_404_no_media(client, fake_evidence_context):
    case_id = fake_evidence_context["case_id"]
    media_id = str(uuid.uuid4())
    creator = fake_evidence_context["creator"]

    mock_investigator = {
        "id": str(uuid.uuid4()),
        "username": creator,
        "role": "ADMIN"
    }
    client.cookies.set(COOKIE_NAME, create_token(mock_investigator))

    response = client.post(f"/api/delete/case/{case_id}/evidence/{media_id}")

    assert response.status_code == 404
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] =="Media not found."
    await assert_object_storage_not_deleted(fake_evidence_context["media_id"],fake_evidence_context["case_id"],fake_evidence_context)

#404: No Case
@pytest.mark.asyncio
async def test_integration_delete_evidence_404_no_case(client, fake_evidence_context):
    case_id = str(uuid.uuid4())
    media_id = fake_evidence_context["media_id"]
    creator = "testerAdmin"

    mock_investigator = {
        "id": str(uuid.uuid4()),
        "username": creator,
        "role": "ADMIN"
    }
    client.cookies.set(COOKIE_NAME, create_token(mock_investigator))

    response = client.post(f"/api/delete/case/{case_id}/evidence/{media_id}")

    assert response.status_code == 404
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] =="Media not found."
    await assert_object_storage_not_deleted(fake_evidence_context["media_id"],fake_evidence_context["case_id"],fake_evidence_context)
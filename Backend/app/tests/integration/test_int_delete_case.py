import pytest
from fastapi.testclient import TestClient
from app.api.main import app
import pytest_asyncio
import asyncpg
import json
import uuid
from app.core.env import Minio_Settings, R2_Settings, Other_Settings
from app.auth.auth import create_token, COOKIE_NAME
from app.tests.integration.test_int_annotations import get_connection, client
import boto3
from botocore.client import Config
from mypy_boto3_s3 import S3Client


minio_settings = Minio_Settings()
r2_settings = R2_Settings()
other_settings = Other_Settings()

def get_object(for_presign: bool = False) -> S3Client:
    if other_settings.ENVIRONMENT == "development":

        if for_presign:
            minio_domain = minio_settings.MINIO_EXTERNAL_URL
        else:
            minio_domain = minio_settings.STORAGE_URL
        
        
        if not minio_domain.startswith(("http://", "https://")):
            minio_domain = f"http://{minio_domain}"

        return boto3.client(
            "s3",
            endpoint_url=minio_domain,
            aws_access_key_id=minio_settings.MINIO_ROOT_USER,
            aws_secret_access_key=minio_settings.MINIO_ROOT_PASSWORD,
            region_name=minio_settings.AWS_REGION,
            config=Config(
                signature_version="s3v4",
                s3={
                    "addressing_style": "path"
                }
            ),
        )

    elif other_settings.ENVIRONMENT == "production":
        cloud_url = r2_settings.R2_URL
        
        if not cloud_url.startswith(("http://", "https://")):
            cloud_url = f"https://{cloud_url}"

        key_id=r2_settings.R2_ACCESS_KEY_ID
        secret=r2_settings.R2_SECRET_ACCESS_KEY

        return boto3.client(
            "s3",
            endpoint_url=cloud_url,
            aws_access_key_id=key_id,
            aws_secret_access_key=secret,
            region_name="auto",
            config=Config(
                signature_version="s3v4",
                s3={
                    "addressing_style": "path"
                }
            ),
        )

@pytest_asyncio.fixture
async def fake_delete_case_context():
    conn = await get_connection()
    storage =  get_object()
    created_ids = {}

    try:
        #fetch the .png incase someone never seeded their db
        media_type_row = await conn.fetchrow(
            """
            SELECT MediaTypeId, MediaBucket, MediaExtension 
            FROM "Cases_DB"."MediaType" 
            WHERE MediaExtension = $1 
            LIMIT 1
            """,
            ".png"
        )
        
        assert media_type_row is not None, "Someone doesn't have there db seeded for media types"
        
        media_type_id = media_type_row["mediatypeid"]
        bucket_name = media_type_row["mediabucket"]
        extension = media_type_row["mediaextension"]

        case_id = str(uuid.uuid4())
        case_creator = "TestInvest"
        await conn.execute(
            """
            INSERT INTO "Cases_DB"."Cases" (CaseId, CaseName, CaseCreator, CaseDescription, CaseClosed)
            VALUES ($1, $2, $3, $4, $5)
            """,
            uuid.UUID(case_id),
            "Integration Test Delete Case",
            case_creator,
            "Case description for deletion test",
            False
        )
        created_ids["case_id"] = case_id

        media_id = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO "Cases_DB"."Media" (MediaId, MediaType, MediaHash)
            VALUES ($1, $2, $3)
            """,
            uuid.UUID(media_id),
            media_type_id,
            uuid.uuid4().hex
        )
        created_ids["media_id"] = media_id

        report_row = await conn.fetchrow(
            """
            INSERT INTO "Cases_DB"."Reports" (CaseId, MediaId, ImageTitle)
            VALUES ($1, $2, $3)
            RETURNING ReportId
            """,
            uuid.UUID(case_id),
            uuid.UUID(media_id),
            "Test Image"
        )
        created_ids["report_id"] = str(report_row["reportid"])

        file_key = f"{media_id}{extension}"
        storage.put_object(
            Bucket=bucket_name,
            Key=file_key,
            Body=b"fake png image byte stream payload"
        )
        created_ids["file_key"] = file_key
        created_ids["bucket"] = bucket_name

        yield {
            "case_id": case_id,
            "case_creator": case_creator,
            "media_id": media_id,
            "file_key": file_key,
            "bucket": bucket_name
        }

    finally:
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

        if "bucket" in created_ids and "file_key" in created_ids:
            try:
                storage.delete_object(
                    Bucket=created_ids["bucket"],
                    Key=created_ids["file_key"]
                )
            except Exception:
                pass

        await conn.close()

#404
@pytest.mark.asyncio
async def test_integration_delete_case_not_found_case(client, fake_delete_case_context):
    case_id = "9b74b4e3-7823-464b-a65f-4df2d75eeab3"
    creator = fake_delete_case_context["case_creator"]

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": creator,
        "role": "INVESTIGATOR"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.request(
        "DELETE",
        "/api/deleteCase",
        json={"CaseID": case_id}
    )

    assert response.status_code == 404
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] == "Case not found"

#403
@pytest.mark.asyncio
async def test_integration_delete_case_user_perms(client, fake_delete_case_context):
    case_id = fake_delete_case_context["case_id"]
    creator = fake_delete_case_context["case_creator"]

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "Pitbull",
        "role": "USER"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.request(
        "DELETE",
        "/api/deleteCase",
        json={"CaseID": case_id}
    )

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] == "User unauthorized"


@pytest.mark.asyncio
async def test_integration_delete_case_not_admin_id(client, fake_delete_case_context):
    case_id = fake_delete_case_context["case_id"]
    creator = fake_delete_case_context["case_creator"]

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "Pitbull",
        "role": "INVESTIGATOR"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.request(
        "DELETE",
        "/api/deleteCase",
        json={"CaseID": case_id}
    )

    assert response.status_code == 403
    assert response.json()["detail"]["status"] == "error"
    assert response.json()["detail"]["message"] == "Only the case creator or an admin can delete this case"

#400
@pytest.mark.asyncio
async def test_integration_delete_case_missing_case_id(client, fake_delete_case_context):
    case_id = ""
    creator = fake_delete_case_context["case_creator"]

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": creator,
        "role": "INVESTIGATOR"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.request(
        "DELETE",
        "/api/deleteCase",
        json={"CaseID": case_id}
    )

    assert response.status_code == 400
    assert response.json()["detail"]["status"] == "error"

    

@pytest.mark.asyncio
async def test_integration_delete_case_success(client, fake_delete_case_context):
    case_id = fake_delete_case_context["case_id"]
    creator = fake_delete_case_context["case_creator"]

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": creator,
        "role": "INVESTIGATOR"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.request(
        "DELETE",
        "/api/deleteCase",
        json={"CaseID": case_id}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"

    conn = await get_connection()
    try:
        case_row = await conn.fetchrow(
            'SELECT * FROM "Cases_DB"."Cases" WHERE CaseId = $1',
            uuid.UUID(case_id)
        )
        assert case_row is None
    finally:
        await conn.close()
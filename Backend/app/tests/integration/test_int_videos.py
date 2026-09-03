from pathlib import Path
from uuid import uuid4

import pytest

from app.tests.integration.conftest import get_connection
from app.core.media_service import get_object
from app.core.video_service import VideoService


TEST_VIDEO = Path(__file__).resolve().parent / "test.mp4"


async def create_test_media(executor_id: str, executor_username: str):
    media_id = uuid4()
    case_id = uuid4()

    connection = await get_connection()

    try:
        await connection.execute(
            "SELECT set_config('app.current_user_id', $1, false)",
            executor_id
        )

        media_type = await connection.fetchrow(
            """
            SELECT
                MediaTypeId,
                MediaBucket,
                MediaExtension
            FROM "Cases_DB"."MediaType"
            WHERE LOWER(MediaExtension) = '.mp4'
            LIMIT 1
            """
        )

        if media_type is None:
            pytest.fail("No MP4 MediaType exists")

        await connection.execute(
            """
            INSERT INTO "Cases_DB"."Cases" (
                CaseId,
                CaseName,
                CaseCreator,
                CaseDescription
            )
            VALUES ($1, $2, $3, $4)
            """,
            case_id,
            "Video Integration Test",
            executor_username,
            "Temporary case for video integration testing."
        )

        await connection.execute(
            """
            INSERT INTO "Cases_DB"."Media" (
                MediaId,
                MediaType
            )
            VALUES ($1, $2)
            """,
            media_id,
            media_type["mediatypeid"]
        )

        await connection.execute(
            """
            INSERT INTO "Cases_DB"."Reports" (
                MediaId,
                CaseId
            )
            VALUES ($1, $2)
            """,
            media_id,
            case_id
        )

        return (
            media_id,
            case_id,
            media_type["mediabucket"],
            media_type["mediaextension"]
        )

    finally:
        await connection.close()

def upload_test_video(media_id, bucket, extension):
    storage_client = get_object()

    object_name = f"{media_id}{extension}"

    with open(TEST_VIDEO, "rb") as file_obj:
        storage_client.upload_fileobj(
            Fileobj=file_obj,
            Bucket=bucket,
            Key=object_name
        )

    return object_name

async def get_report(media_id):
    connection = await get_connection()

    try:
        return await connection.fetchrow(
            """
            SELECT
                ReportArtifacts,
                ReportFindings,
                ReportCertainty
            FROM "Cases_DB"."Reports"
            WHERE MediaId = $1
            """,
            media_id
        )

    finally:
        await connection.close()

async def delete_test_data(
    media_id,
    case_id,
    bucket,
    object_name,
    executor_id
):
    storage_client = get_object()
    storage_client.delete_object(Bucket=bucket, Key=object_name)
    connection = await get_connection()

    try:
        await connection.execute(
            "SELECT set_config('app.current_user_id', $1, false)",
            executor_id
        )

        await connection.execute(
            """
            DELETE FROM "Cases_DB"."Reports"
            WHERE MediaId = $1
            """,
            media_id
        )

        await connection.execute(
            """
            DELETE FROM "Cases_DB"."Media"
            WHERE MediaId = $1
            """,
            media_id
        )

        await connection.execute(
            """
            DELETE FROM "Cases_DB"."Cases"
            WHERE CaseId = $1
            """,
            case_id
        )

    finally:
        await connection.close()

@pytest.mark.asyncio
async def test_video_full_integration(ensure_user_exists):
    service = VideoService()

    executor_id = str(uuid4())
    base_username = "video_integration_user"

    executor_username = f"{base_username}_{executor_id[:8]}"

    media_id = None
    case_id = None
    bucket = None
    object_name = None

    connection = await get_connection()

    try:
        await ensure_user_exists(
            connection,
            executor_id,
            base_username
        )
    finally:
        await connection.close()

    try:
        (
            media_id,
            case_id,
            bucket,
            extension
        ) = await create_test_media(
            executor_id,
            executor_username
        )

        object_name = upload_test_video(
            media_id,
            bucket,
            extension
        )

        result = await service.analyse(media_id)

        assert result is not None

        assert "risk_level" in result
        assert "ai_probability" in result
        assert "prediction" in result
        assert "findings" in result

        assert 0.0 <= result["ai_probability"] <= 1.0

        assert result["prediction"] in ("AI-generated", "Authentic")

        assert result["risk_level"] in (0, 1, 2, 3)
        assert "visual" in result
        assert "audio" in result
        assert "fusion" in result

        visual = result["visual"]

        assert "prediction" in visual
        assert "ai_probability" in visual
        assert "authentic_probability" in visual
        assert "frame_importance" in visual
        assert 0.0 <= visual["ai_probability"] <= 1.0
        assert visual["prediction"] in ("AI-generated", "Authentic")

        audio = result["audio"]

        assert "available" in audio

        if audio["available"]:
            assert "prediction" in audio
            assert "ai_probability" in audio
            assert 0.0 <= audio["ai_probability"] <= 1.0
            assert audio["prediction"] in ("AI-generated", "Authentic")

        fusion = result["fusion"]

        assert "visual_weight" in fusion
        assert "audio_weight" in fusion

        report = await get_report(media_id)

        assert report is not None
        assert report["reportartifacts"] is not None
        assert report["reportfindings"] is not None
        assert report["reportcertainty"] is not None

        assert "Metadata:" in report["reportfindings"]
        assert "AI Video Classifier:" in report["reportfindings"]
        assert "Visual Analysis:" in report["reportfindings"]
        assert "Audio Analysis:" in report["reportfindings"]
        assert "Combined Analysis:" in report["reportfindings"]

    finally:
        if media_id is not None and case_id is not None and bucket is not None and object_name is not None:
            await delete_test_data(
                media_id,
                case_id,
                bucket,
                object_name,
                executor_id
            )
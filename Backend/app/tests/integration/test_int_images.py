from pathlib import Path
from uuid import UUID, uuid4
import json
import pytest
from app.tests.integration.conftest import get_connection
from app.core.media_service import get_object
from app.core.image_service import ImageService

TEST_IMAGE = Path(__file__).resolve().parent / "test.png"

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


async def create_test_media(
    executor_id: str,
    executor_username: str
):
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
            WHERE LOWER(MediaExtension) IN ('.jpg', '.jpeg')
            LIMIT 1
            """
        )

        if media_type is None:
            pytest.fail("No JPG/JPEG MediaType exists")

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
            "Image Integration Test",
            executor_username,
            "Temporary case for image integration testing."
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

        return (
            media_id,
            case_id,
            media_type["mediabucket"],
            media_type["mediaextension"]
        )

    finally:
        await connection.close()


def upload_test_image(
    media_id,
    bucket,
    extension
):
    storage_client = get_object()

    object_name = f"{media_id}{extension}"

    with open(TEST_IMAGE, "rb") as file_obj:
        storage_client.upload_fileobj(
            Fileobj=file_obj,
            Bucket=bucket,
            Key=object_name,
            ExtraArgs={
                "ContentType": "image/jpeg"
            }
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
            FROM "Cases_DB"."Media"
            WHERE MediaId = $1
            """,
            media_id
        )

    finally:
        await connection.close()


def heatmap_exists(media_id):
    storage_client = get_object()

    try:
        storage_client.head_object(
            Bucket="heatmaps",
            Key=f"{media_id}.png"
        )

        return True

    except Exception:
        return False


async def delete_test_data(
    media_id,
    case_id,
    bucket,
    object_name,
    executor_id
):
    storage_client = get_object()

    storage_client.delete_object(
        Bucket=bucket,
        Key=object_name
    )

    storage_client.delete_object(
        Bucket="heatmaps",
        Key=f"{media_id}.png"
    )

    connection = await get_connection()

    try:
        await connection.execute(
            "SELECT set_config('app.current_user_id', $1, false)",
            executor_id
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
async def test_image_full_integration(
    ensure_user_exists
):
    service = ImageService()

    executor_id = str(uuid4())
    base_username = "image_integration_user"

    executor_username = (
        f"{base_username}_{executor_id[:8]}"
    )

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

        object_name = upload_test_image(
            media_id,
            bucket,
            extension
        )

        result = await service.analyse(media_id)

        assert result is not None

        assert "risk_level" in result
        assert "ai_probability" in result
        assert "classification" in result
        assert "findings" in result

        assert result["risk_level"] in (0, 1, 2, 3)

        report = await get_report(media_id)

        assert report is not None
        assert report["reportartifacts"] is not None
        assert report["reportfindings"] is not None
        assert report["reportcertainty"] is not None

        assert "Metadata:" in report["reportfindings"]
        assert "Binary Classifier:" in report["reportfindings"]

        # Heatmap should have been persisted to MinIO.
        assert heatmap_exists(media_id)

        annotation_record = (
            await get_automated_annotations(media_id)
        )

        assert annotation_record is not None
        assert annotation_record["mediaid"] == media_id
        assert annotation_record["mediaannotations"] is not None
        assert annotation_record["createdat"] is not None

        annotations = annotation_record["mediaannotations"]

        if isinstance(annotations, str):
            annotations = json.loads(annotations)

        assert isinstance(annotations, list)

        # ImageService currently creates at most one
        # heatmap-derived annotation.
        assert len(annotations) <= 1

        for annotation in annotations:
            assert "id" in annotation
            UUID(annotation["id"])

            assert annotation["kind"] == "shape"
            assert annotation["source"] == "AI"

            assert "points" in annotation
            assert isinstance(annotation["points"], list)
            assert len(annotation["points"]) == 5

            assert (
                annotation["points"][0]
                == annotation["points"][-1]
            )

            for point in annotation["points"]:
                assert "x" in point
                assert "y" in point

                assert 0 <= point["x"] <= 100
                assert 0 <= point["y"] <= 100

            # Images should not need video timestamps.
            assert "timeStamp" not in annotation

    finally:
        if (
            media_id is not None
            and case_id is not None
            and bucket is not None
            and object_name is not None
        ):
            await delete_test_data(
                media_id,
                case_id,
                bucket,
                object_name,
                executor_id
            )
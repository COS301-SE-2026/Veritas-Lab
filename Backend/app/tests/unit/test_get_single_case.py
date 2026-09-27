import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import asyncpg
import pytest
from fastapi import HTTPException
from app.api.routers.cases_router import get_single_case

def make_case_row(
    case_id=None,
    creator="test_user",
    state="OPEN",
    assigned=None
):
    if case_id is None:
        case_id = uuid.uuid4()

    return {
        "caseid": case_id,
        "casecreator": creator,
        "casename": "Test Case",
        "casedescription": "Test case description",
        "casestate": state,
        "casecreationdate": "2026-09-15T10:00:00+00:00",
        "caseassigned": assigned
    }

def make_evidence_row(
    media_id=None,
    pnp_model_id=None,
    pnp_model_name=None,
    pnp_model_result=None,
    pnp_upload_date=None
):
    if media_id is None:
        media_id = uuid.uuid4()

    return {
        "mediaid": media_id,
        "caseperspective": "Front view",
        "annotations": [],
        "automatedannotations": [],
        "reportartifacts": {},
        "reportfindings": '["No manipulation detected"]',
        "reportcomments": "Reviewed",
        "reportcertainty": 3,
        "reportdatecreation": None,
        "mediauploaddate": None,
        "mediatypeid": uuid.uuid4(),
        "medianame": "test.jpg",
        "mediaextension": ".jpg",
        "mediabucket": "images",
        "pnpmodelid": pnp_model_id,
        "pnpmodelname": pnp_model_name,
        "pnpmodelresult": pnp_model_result,
        "pnpuploaddate": pnp_upload_date
    }

def make_case_object():
    case = MagicMock()
    case.to_json.return_value = {
        "caseId": "case-id",
        "caseName": "Test Case",
        "caseCreator": "test_user",
        "caseDescription": "Test case description",
        "caseState": "OPEN"
    }

    case.get_comments = AsyncMock(return_value=[])
    return case

@pytest.mark.asyncio
async def test_get_single_case_user_success_hides_report():
    case_id = str(uuid.uuid4())
    connection = MagicMock()
    connection.fetchrow = AsyncMock(
        return_value=make_case_row(
            case_id=uuid.UUID(case_id),
            creator="test_user",
            state="OPEN"
        )
    )
    connection.fetch = AsyncMock(return_value=[make_evidence_row()])

    mock_case = make_case_object()

    with patch(
        "app.api.routers.cases_router.verify_jwt",
        return_value={
            "sub": "user-id-1",
            "username": "test_user",
            "role": "USER"
        }
    ), patch(
        "app.api.routers.cases_router.Case"
    ) as mock_case_class, patch(
        "app.api.routers.cases_router._row_to_case",
        return_value=mock_case
    ), patch(
        "app.api.routers.cases_router._format_case_evidence",
        return_value={
            "mediaId": "media-id",
            "mediaName": "test.jpg"
        }
    ) as mock_format:
        mock_case_class.return_value.case_id = uuid.UUID(case_id)

        response = await get_single_case(
            case_id=case_id,
            request=MagicMock(),
            connection=connection
        )

    assert response["status"] == "success"
    assert response["comments"] == []
    assert len(response["evidence"]) == 1
    mock_format.assert_called_once()
    assert mock_format.call_args.kwargs["include_report"] is False
    assert mock_format.call_args.kwargs["plug_and_play"] == []

@pytest.mark.asyncio
async def test_get_single_case_investigator_success_shows_report():
    case_id = str(uuid.uuid4())
    connection = MagicMock()
    connection.fetchrow = AsyncMock(
        return_value=make_case_row(
            case_id=uuid.UUID(case_id),
            creator="another_user",
            state="PUBLISHED",
            assigned=None
        )
    )

    connection.fetch = AsyncMock(return_value=[make_evidence_row()])
    mock_case = make_case_object()

    with patch(
        "app.api.routers.cases_router.verify_jwt",
        return_value={
            "sub": "investigator-id",
            "username": "investigator1",
            "role": "INVESTIGATOR"
        }
    ), patch(
        "app.api.routers.cases_router.Case"
    ) as mock_case_class, patch(
        "app.api.routers.cases_router._row_to_case",
        return_value=mock_case
    ), patch(
        "app.api.routers.cases_router._format_case_evidence",
        return_value={
            "mediaId": "media-id",
            "reportFindings": "No manipulation detected"
        }
    ) as mock_format:
        mock_case_class.return_value.case_id = uuid.UUID(case_id)

        response = await get_single_case(
            case_id=case_id,
            request=MagicMock(),
            connection=connection
        )

    assert response["status"] == "success"
    mock_format.assert_called_once()
    assert mock_format.call_args.kwargs["include_report"] is True

@pytest.mark.asyncio
async def test_get_single_case_admin_success_shows_report():
    case_id = str(uuid.uuid4())
    connection = MagicMock()
    connection.fetchrow = AsyncMock(
        return_value=make_case_row(
            case_id=uuid.UUID(case_id),
            creator="another_user",
            state="PUBLISHED"
        )
    )

    connection.fetch = AsyncMock(return_value=[make_evidence_row()])
    mock_case = make_case_object()

    with patch(
        "app.api.routers.cases_router.verify_jwt",
        return_value={
            "sub": "admin-id",
            "username": "admin1",
            "role": "ADMIN"
        }
    ), patch(
        "app.api.routers.cases_router.Case"
    ) as mock_case_class, patch(
        "app.api.routers.cases_router._row_to_case",
        return_value=mock_case
    ), patch(
        "app.api.routers.cases_router._format_case_evidence",
        return_value={
            "mediaId": "media-id",
            "reportFindings": "No manipulation detected"
        }
    ) as mock_format:
        mock_case_class.return_value.case_id = uuid.UUID(case_id)

        response = await get_single_case(
            case_id=case_id,
            request=MagicMock(),
            connection=connection
        )

    assert response["status"] == "success"
    assert mock_format.call_args.kwargs["include_report"] is True
    assert mock_format.call_args.kwargs["plug_and_play"] == []

@pytest.mark.asyncio
async def test_get_single_case_not_found():
    case_id = str(uuid.uuid4())
    connection = MagicMock()
    connection.fetchrow = AsyncMock(return_value=None)
    connection.fetch = AsyncMock()

    with patch(
        "app.api.routers.cases_router.verify_jwt",
        return_value={
            "sub": "user-id",
            "username": "test_user",
            "role": "USER"
        }
    ), patch(
        "app.api.routers.cases_router.Case"
    ) as mock_case_class:
        mock_case_class.return_value.case_id = uuid.UUID(case_id)

        with pytest.raises(HTTPException) as exc_info:
            await get_single_case(
                case_id=case_id,
                request=MagicMock(),
                connection=connection
            )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == {
        "status": "error",
        "message": "Case not found"
    }
    connection.fetch.assert_not_called()

@pytest.mark.asyncio
async def test_get_single_case_database_error_fetching_case():
    case_id = str(uuid.uuid4())
    connection = MagicMock()
    connection.fetchrow = AsyncMock(side_effect=asyncpg.PostgresError("Database failure"))

    with patch(
        "app.api.routers.cases_router.verify_jwt",
        return_value={
            "sub": "user-id",
            "username": "test_user",
            "role": "USER"
        }
    ), patch(
        "app.api.routers.cases_router.Case"
    ) as mock_case_class:
        mock_case_class.return_value.case_id = uuid.UUID(case_id)

        with pytest.raises(HTTPException) as exc_info:
            await get_single_case(
                case_id=case_id,
                request=MagicMock(),
                connection=connection
            )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == {
        "status": "error",
        "message": "Database error"
    }

@pytest.mark.asyncio
async def test_get_single_case_database_error_fetching_evidence():
    case_id = str(uuid.uuid4())
    connection = MagicMock()
    connection.fetchrow = AsyncMock(
        return_value=make_case_row(
            case_id=uuid.UUID(case_id),
            creator="test_user",
            state="OPEN"
        )
    )

    connection.fetch = AsyncMock(side_effect=asyncpg.PostgresError("Database failure"))
    mock_case = make_case_object()

    with patch(
        "app.api.routers.cases_router.verify_jwt",
        return_value={
            "sub": "user-id",
            "username": "test_user",
            "role": "USER"
        }
    ), patch(
        "app.api.routers.cases_router.Case"
    ) as mock_case_class, patch(
        "app.api.routers.cases_router._row_to_case",
        return_value=mock_case
    ):
        mock_case_class.return_value.case_id = uuid.UUID(case_id)

        with pytest.raises(HTTPException) as exc_info:
            await get_single_case(
                case_id=case_id,
                request=MagicMock(),
                connection=connection
            )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == {
        "status": "error",
        "message": "Database error"
    }

@pytest.mark.asyncio
async def test_get_single_case_groups_multiple_pnp_models_for_same_media():
    case_id = str(uuid.uuid4())
    media_id = uuid.uuid4()

    connection = MagicMock()
    connection.fetchrow = AsyncMock(
        return_value=make_case_row(
            case_id=uuid.UUID(case_id),
            creator="another_user",
            state="PUBLISHED"
        )
    )

    connection.fetch = AsyncMock(
        return_value=[
            make_evidence_row(
                media_id=media_id,
                pnp_model_id=1,
                pnp_model_name="ModelA",
                pnp_model_result='{"classification": "AI", "confidence": 0.91}',
                pnp_upload_date=None
            ),
            make_evidence_row(
                media_id=media_id,
                pnp_model_id=2,
                pnp_model_name="ModelB",
                pnp_model_result='{"classification": "AUTHENTIC", "confidence": 0.87}',
                pnp_upload_date=None
            )
        ]
    )

    mock_case = make_case_object()

    with patch(
        "app.api.routers.cases_router.verify_jwt",
        return_value={
            "sub": "investigator-id",
            "username": "investigator1",
            "role": "INVESTIGATOR"
        }
    ), patch(
        "app.api.routers.cases_router.Case"
    ) as mock_case_class, patch(
        "app.api.routers.cases_router._row_to_case",
        return_value=mock_case
    ), patch(
        "app.api.routers.cases_router._format_case_evidence",
        return_value={
            "mediaId": str(media_id),
            "plugAndPlay": []
        }
    ) as mock_format:
        mock_case_class.return_value.case_id = uuid.UUID(case_id)

        response = await get_single_case(
            case_id=case_id,
            request=MagicMock(),
            connection=connection
        )

    assert response["status"] == "success"
    assert len(response["evidence"]) == 1

    plug_and_play = mock_format.call_args.kwargs["plug_and_play"]

    assert len(plug_and_play) == 2

    assert plug_and_play[0]["PNPModelId"] == 1
    assert plug_and_play[0]["mediaId"] == str(media_id)
    assert plug_and_play[0]["modelName"] == "ModelA"
    assert plug_and_play[0]["modelResult"]["classification"] == "AI"
    assert plug_and_play[0]["modelResult"]["confidence"] == 0.91

    assert plug_and_play[1]["PNPModelId"] == 2
    assert plug_and_play[1]["modelName"] == "ModelB"
    assert plug_and_play[1]["modelResult"]["classification"] == "AUTHENTIC"
    assert plug_and_play[1]["modelResult"]["confidence"] == 0.87

@pytest.mark.asyncio
async def test_get_single_case_keeps_pnp_models_separate_per_media():
    case_id = str(uuid.uuid4())
    media_id_1 = uuid.uuid4()
    media_id_2 = uuid.uuid4()

    connection = MagicMock()
    connection.fetchrow = AsyncMock(
        return_value=make_case_row(
            case_id=uuid.UUID(case_id),
            creator="another_user",
            state="PUBLISHED"
        )
    )

    connection.fetch = AsyncMock(
        return_value=[
            make_evidence_row(
                media_id=media_id_1,
                pnp_model_id=1,
                pnp_model_name="ImageModel",
                pnp_model_result='{"classification": "AI"}'
            ),
            make_evidence_row(
                media_id=media_id_2,
                pnp_model_id=2,
                pnp_model_name="VideoModel",
                pnp_model_result='{"classification": "AUTHENTIC"}'
            )
        ]
    )

    mock_case = make_case_object()

    with patch(
        "app.api.routers.cases_router.verify_jwt",
        return_value={
            "sub": "admin-id",
            "username": "admin1",
            "role": "ADMIN"
        }
    ), patch(
        "app.api.routers.cases_router.Case"
    ) as mock_case_class, patch(
        "app.api.routers.cases_router._row_to_case",
        return_value=mock_case
    ), patch(
        "app.api.routers.cases_router._format_case_evidence",
        side_effect=lambda row, include_report, plug_and_play: {
            "mediaId": str(row["mediaid"]),
            "plugAndPlay": plug_and_play
        }
    ):
        mock_case_class.return_value.case_id = uuid.UUID(case_id)

        response = await get_single_case(
            case_id=case_id,
            request=MagicMock(),
            connection=connection
        )

    assert len(response["evidence"]) == 2

    evidence_by_id = {
        item["mediaId"]: item
        for item in response["evidence"]
    }

    assert len(evidence_by_id[str(media_id_1)]["plugAndPlay"]) == 1
    assert evidence_by_id[str(media_id_1)]["plugAndPlay"][0]["modelName"] == "ImageModel"

    assert len(evidence_by_id[str(media_id_2)]["plugAndPlay"]) == 1
    assert evidence_by_id[str(media_id_2)]["plugAndPlay"][0]["modelName"] == "VideoModel"

def test_format_case_evidence_hides_pnp_when_report_not_visible():
    row = make_evidence_row()

    with patch(
        "app.api.routers.cases_router.get_object"
    ) as mock_get_object:
        presign_client = MagicMock()
        presign_client.generate_presigned_url.return_value = "https://example.com/file"

        mock_get_object.return_value = presign_client

        from app.api.routers.cases_router import _format_case_evidence

        result = _format_case_evidence(
            row,
            include_report=False,
            plug_and_play=[
                {
                    "PNPModelId": 1,
                    "mediaId": str(row["mediaid"]),
                    "modelName": "TestModel",
                    "modelResult": {},
                    "uploadDate": None
                }
            ]
        )

    assert "plugAndPlay" not in result

def test_format_case_evidence_shows_pnp_when_report_visible():
    row = make_evidence_row()

    plug_and_play = [
        {
            "PNPModelId": 1,
            "mediaId": str(row["mediaid"]),
            "modelName": "TestModel",
            "modelResult": {
                "classification": "AI"
            },
            "uploadDate": None
        }
    ]

    with patch(
        "app.api.routers.cases_router.get_object"
    ) as mock_get_object:
        presign_client = MagicMock()
        presign_client.generate_presigned_url.return_value = "https://example.com/file"

        mock_get_object.return_value = presign_client

        from app.api.routers.cases_router import _format_case_evidence

        result = _format_case_evidence(
            row,
            include_report=True,
            plug_and_play=plug_and_play
        )

    assert result["plugAndPlay"] == plug_and_play
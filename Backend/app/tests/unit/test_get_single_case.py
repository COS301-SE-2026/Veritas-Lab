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

def make_evidence_row():
    return {
        "mediaid": uuid.uuid4(),
        "caseperspective": "Front view",
        "annotations": [],
        "reportartifacts": {},
        "reportfindings": "No manipulation detected",
        "reportcomments": "Reviewed",
        "reportcertainty": 3,
        "reportdatecreation": "2026-09-15T11:00:00+00:00",
        "mediauploaddate": "2026-09-15T09:00:00+00:00",
        "mediatypeid": uuid.uuid4(),
        "medianame": "test.jpg",
        "mediaextension": ".jpg",
        "mediabucket": "images"
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
            CaseId=case_id,
            request=MagicMock(),
            connection=connection
        )

    assert response["status"] == "success"
    assert response["comments"] == []
    assert len(response["evidence"]) == 1
    mock_format.assert_called_once()
    assert mock_format.call_args.kwargs["include_report"] is False

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
            CaseId=case_id,
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
            CaseId=case_id,
            request=MagicMock(),
            connection=connection
        )

    assert response["status"] == "success"
    assert mock_format.call_args.kwargs["include_report"] is True

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
                CaseId=case_id,
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
                CaseId=case_id,
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
                CaseId=case_id,
                request=MagicMock(),
                connection=connection
            )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == {
        "status": "error",
        "message": "Database error"
    }
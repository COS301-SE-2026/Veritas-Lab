from unittest.mock import AsyncMock, MagicMock, patch
import asyncpg
import pytest
from fastapi import HTTPException
from app.api.routers.cases_router import DATABASE_ERROR_MESSAGE, get_cases

def make_case_row(
    case_id="12345678-abcd-ef01-2345-6789abcdef01",
    creator="test_user",
    name="Test Case",
    description="Test description",
    state="OPEN",
    creation_date="2026-09-15T10:00:00+00:00"
):
    return {
        "caseid": case_id,
        "casecreator": creator,
        "casename": name,
        "casedescription": description,
        "casestate": state,
        "casecreationdate": creation_date
    }

def make_case_object(
    case_id="12345678-abcd-ef01-2345-6789abcdef01",
    creator="test_user",
    state="OPEN"
):
    case = MagicMock()

    case.to_json.return_value = {
        "caseId": case_id,
        "caseName": "Test Case",
        "caseCreator": creator,
        "caseDescription": "Test description",
        "caseState": state,
        "caseCreationDate": "2026-09-15T10:00:00+00:00"
    }

    return case

@pytest.mark.asyncio
async def test_get_cases_user_success():
    connection = MagicMock()
    row = make_case_row(creator="test_user", state="OPEN")
    connection.fetch = AsyncMock(return_value=[row])
    mock_case = make_case_object(creator="test_user",state="OPEN")

    with patch(
        "app.api.routers.cases_router.verify_jwt",
        return_value={
            "sub": "user-id",
            "username": "test_user",
            "role": "USER"
        }
    ), patch(
        "app.api.routers.cases_router._row_to_case",
        return_value=mock_case
    ) as mock_row_to_case:

        response = await get_cases(
            request=MagicMock(),
            connection=connection
        )

    assert response["status"] == "success"
    assert len(response["cases"]) == 1

    assert response["cases"][0]["caseCreator"] == "test_user"
    assert response["cases"][0]["caseState"] == "OPEN"

    mock_row_to_case.assert_called_once_with(row)
    connection.fetch.assert_awaited_once()
    args = connection.fetch.call_args.args

    assert args[1] == "test_user"

@pytest.mark.asyncio
async def test_get_cases_investigator_success():
    connection = MagicMock()

    rows = [
        make_case_row(
            creator="investigator1",
            state="OPEN"
        ),
        make_case_row(
            case_id="22345678-abcd-ef01-2345-6789abcdef01",
            creator="another_user",
            state="PUBLISHED"
        )
    ]

    connection.fetch = AsyncMock(return_value=rows)

    own_case = make_case_object(creator="investigator1",state="OPEN")

    published_case = make_case_object(
        case_id="22345678-abcd-ef01-2345-6789abcdef01",
        creator="another_user",
        state="PUBLISHED"
    )

    with patch(
        "app.api.routers.cases_router.verify_jwt",
        return_value={
            "sub": "investigator-id",
            "username": "investigator1",
            "role": "INVESTIGATOR"
        }
    ), patch(
        "app.api.routers.cases_router._row_to_case",
        side_effect=[
            own_case,
            published_case
        ]
    ):

        response = await get_cases(
            request=MagicMock(),
            connection=connection
        )

    assert response["status"] == "success"
    assert len(response["cases"]) == 2
    assert response["cases"][0]["caseCreator"] == "investigator1"
    assert response["cases"][0]["caseState"] == "OPEN"
    assert response["cases"][1]["caseCreator"] == "another_user"
    assert response["cases"][1]["caseState"] == "PUBLISHED"

    args = connection.fetch.call_args.args

    assert args[1] == "investigator1"

@pytest.mark.asyncio
async def test_get_cases_admin_success():
    connection = MagicMock()

    rows = [
        make_case_row(
            creator="another_user",
            state="CLOSED"
        )
    ]

    connection.fetch = AsyncMock(return_value=rows)

    mock_case = make_case_object(creator="another_user",state="CLOSED")

    with patch(
        "app.api.routers.cases_router.verify_jwt",
        return_value={
            "sub": "admin-id",
            "username": "admin1",
            "role": "ADMIN"
        }
    ), patch(
        "app.api.routers.cases_router._row_to_case",
        return_value=mock_case
    ):

        response = await get_cases(
            request=MagicMock(),
            connection=connection
        )

    assert response["status"] == "success"
    assert len(response["cases"]) == 1
    assert response["cases"][0]["caseCreator"] == "another_user"
    assert response["cases"][0]["caseState"] == "CLOSED"

    args = connection.fetch.call_args.args

    assert args[1] == "admin1"

@pytest.mark.asyncio
async def test_get_cases_empty_result():
    connection = MagicMock()

    connection.fetch = AsyncMock(
        return_value=[]
    )

    with patch(
        "app.api.routers.cases_router.verify_jwt",
        return_value={
            "sub": "user-id",
            "username": "test_user",
            "role": "USER"
        }
    ), patch(
        "app.api.routers.cases_router._row_to_case"
    ) as mock_row_to_case:

        response = await get_cases(
            request=MagicMock(),
            connection=connection
        )

    assert response == {
        "status": "success",
        "cases": []
    }

    mock_row_to_case.assert_not_called()

@pytest.mark.asyncio
async def test_get_cases_database_error():
    connection = MagicMock()

    connection.fetch = AsyncMock(
        side_effect=asyncpg.PostgresError(
            "Database failure"
        )
    )

    with patch(
        "app.api.routers.cases_router.verify_jwt",
        return_value={
            "sub": "user-id",
            "username": "test_user",
            "role": "USER"
        }
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_cases(
                request=MagicMock(),
                connection=connection
            )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == {
        "status": "error",
        "message": DATABASE_ERROR_MESSAGE
    }
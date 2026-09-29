import pytest
import asyncpg

from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.api.routers.cases_router import assign_case, assign_case_request

def mock_transaction(connection):
    transaction = MagicMock()
    transaction.__aenter__ = AsyncMock(return_value=None)
    transaction.__aexit__ = AsyncMock(return_value=None)

    connection.transaction.return_value = transaction

@pytest.mark.asyncio
async def test_assign_case_success():
    request = MagicMock()
    connection = MagicMock()
    connection.fetchrow = AsyncMock()

    mock_transaction(connection)

    assign_request = assign_case_request(
        CaseID="550e8400-e29b-41d4-a716-446655440000"
    )

    connection.fetchrow.return_value = {
        "caseid": "550e8400-e29b-41d4-a716-446655440000",
        "caseassigned": "investigator1",
        "casestate": "PUBLISHED"
    }

    with patch(
        "app.api.routers.cases_router.verify_jwt",
        return_value={
            "sub": "user-id-1",
            "role": "INVESTIGATOR",
            "username": "investigator1"
        }
    ), patch(
        "app.api.routers.cases_router.set_audit_executor",
        new_callable=AsyncMock
    ) as mock_audit:

        response = await assign_case(
            assign_request,
            request,
            connection
        )

    assert response == {
        "status": "success",
        "message": "Case assigned successfully"
    }

    mock_audit.assert_awaited_once_with(
        connection,
        "user-id-1"
    )

    connection.fetchrow.assert_awaited_once()

@pytest.mark.asyncio
async def test_assign_case_user_forbidden():
    request = MagicMock()
    connection = MagicMock()
    connection.fetchrow = AsyncMock()

    assign_request = assign_case_request(
        CaseID="550e8400-e29b-41d4-a716-446655440000"
    )

    with patch(
        "app.api.routers.cases_router.verify_jwt",
        return_value={
            "sub": "user-id-1",
            "role": "USER",
            "username": "normal_user"
        }
    ):
        with pytest.raises(HTTPException) as exc:
            await assign_case(
                assign_request,
                request,
                connection
            )

    assert exc.value.status_code == 403
    assert exc.value.detail == {
        "status": "error",
        "message": "User unauthorized"
    }

    connection.fetchrow.assert_not_awaited()

@pytest.mark.asyncio
async def test_assign_case_missing_case_id():
    request = MagicMock()
    connection = MagicMock()
    connection.fetchrow = AsyncMock()

    assign_request = assign_case_request(CaseID=None)

    with patch(
        "app.api.routers.cases_router.verify_jwt",
        return_value={
            "sub": "user-id-1",
            "role": "INVESTIGATOR",
            "username": "investigator1"
        }
    ):
        with pytest.raises(HTTPException) as exc:
            await assign_case(
                assign_request,
                request,
                connection
            )

    assert exc.value.status_code == 400
    assert exc.value.detail == {
        "status": "error",
        "message": "CaseID required"
    }

    connection.fetchrow.assert_not_awaited()

@pytest.mark.asyncio
async def test_assign_case_invalid_assignment():
    request = MagicMock()
    connection = MagicMock()
    connection.fetchrow = AsyncMock(return_value=None)

    mock_transaction(connection)

    assign_request = assign_case_request(
        CaseID="550e8400-e29b-41d4-a716-446655440000"
    )

    with patch(
        "app.api.routers.cases_router.verify_jwt",
        return_value={
            "sub": "user-id-1",
            "role": "ADMIN",
            "username": "admin1"
        }
    ), patch(
        "app.api.routers.cases_router.set_audit_executor",
        new_callable=AsyncMock
    ):
        with pytest.raises(HTTPException) as exc:
            await assign_case(
                assign_request,
                request,
                connection
            )

    assert exc.value.status_code == 400
    assert exc.value.detail == {
        "status": "error",
        "message": "Invalid assignment request"
    }

    connection.fetchrow.assert_awaited_once()

@pytest.mark.asyncio
async def test_assign_case_database_error():
    request = MagicMock()
    connection = MagicMock()
    connection.fetchrow = AsyncMock(
        side_effect=asyncpg.PostgresError("Database failed")
    )

    mock_transaction(connection)

    assign_request = assign_case_request(
        CaseID="550e8400-e29b-41d4-a716-446655440000"
    )

    with patch(
        "app.api.routers.cases_router.verify_jwt",
        return_value={
            "sub": "user-id-1",
            "role": "INVESTIGATOR",
            "username": "investigator1"
        }
    ), patch(
        "app.api.routers.cases_router.set_audit_executor",
        new_callable=AsyncMock
    ):
        with pytest.raises(HTTPException) as exc:
            await assign_case(
                assign_request,
                request,
                connection
            )

    assert exc.value.status_code == 500
    assert exc.value.detail == {
        "status": "error",
        "message": "Database error"
    }

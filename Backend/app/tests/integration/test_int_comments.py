import pytest
from fastapi.testclient import TestClient
from app.api.main import app
from app.core.env import User_Settings, Postgres_Settings
import pytest_asyncio
import asyncpg
import json
import uuid
from app.auth.auth import create_token, COOKIE_NAME 

USER_SETTINGS=User_Settings()
POSTGRES_SEETTINGS=Postgres_Settings()

async def get_connection() -> asyncpg.Connection:
    return await asyncpg.connect(
        user=POSTGRES_SEETTINGS.DB_USER,
        password=POSTGRES_SEETTINGS.DB_PASSWORD,
        database=POSTGRES_SEETTINGS.DB_NAME,
        host=POSTGRES_SEETTINGS.DB_HOST,
        port=POSTGRES_SEETTINGS.DB_PORT,
        ssl="require" if POSTGRES_SEETTINGS.DB_SSL else None,
    )

#Test suite for get comments endpoint:


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest_asyncio.fixture
async def fake_comment_context():
    conn = await get_connection()
    created_ids={}

    try:
        case_id1=str(uuid.uuid4())
        case_creation_literal="""
        INSERT INTO "Cases_DB"."Cases" (CaseId, CaseName, CaseCreator, CaseDescription, CaseClosed)
        VALUES ($1, $2, $3, $4, $5)
        """

        await conn.execute(
            case_creation_literal,
            uuid.UUID(case_id1), "Test Case","Creator","To test comments", False
        )

        created_ids["case_id1"]=case_id1

        case_id2=str(uuid.uuid4())
        await conn.execute(
            case_creation_literal,
            uuid.UUID(case_id2), "Test separation", "TestInvest", "For more Tests", True
        )

        comment_creation_literal="""
        INSERT INTO "Cases_DB"."Comments" (CaseId,Username,Comment)
        VALUES ($1,$2,$3)
        RETURNING CommentID
        """

        comment_1_user="Creator"
        comment_1_comment="Checking if you receive this message"
        row = await conn.fetchrow(
            comment_creation_literal,
            case_id1,
            comment_1_user,
            comment_1_comment
        )
        comment_id1=row["commentid"]

        comment_2_comment="Nothing"
        comment_2_user="TestInvest"
        row = await conn.fetchrow(
            comment_creation_literal,
            case_id1,
            comment_2_user,
            comment_2_comment
        )
        comment_id2=row["commentid"]

        yield {
            "case_id1": case_id1,
            "case_id2": case_id2,
            "comment_id1": comment_id1,
            "comment_1_user": comment_1_user,
            "comment_1_comment": comment_1_comment,
            "comment_id2": comment_id2,
            "comment_2_user": comment_2_user,
            "comment_2_comment": comment_2_comment,
        }


    finally:
        delete_case="""
        DELETE FROM "Cases_DB"."Cases" WHERE CaseId= $1
        """
        # Deletes cascade so this should delete the comments as while
        if 'case_id1' in locals():
            await conn.execute(
                delete_case,
                uuid.UUID(case_id1)
            )
        if 'case_id2' in locals():
            await conn.execute(
                delete_case,
                uuid.UUID(case_id2)
            )
        await conn.close()


# - 200: Ideal, The outcome is how we want it to look.

@pytest.mark.asyncio
async def test_integration_get_comment_multiple_success(client, fake_comment_context):
    case_id= fake_comment_context["case_id1"]

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "INVESTIGATOR"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.post(f"/api/getComments/{case_id}")

    assert response.status_code == 200
    assert response.json()["status"] == "success"

    assert len(response.json()["comments"]) == 2
    first_comment=response.json()["comments"][0]

    assert first_comment["commentid"]==fake_comment_context["comment_id1"]
    assert first_comment["username"]==fake_comment_context["comment_1_user"]
    assert first_comment["comment"]==fake_comment_context["comment_1_comment"]

    second_comment=response.json()["comments"][1]

    assert second_comment["commentid"]==fake_comment_context["comment_id2"]
    assert second_comment["username"]==fake_comment_context["comment_2_user"]
    assert second_comment["comment"]==fake_comment_context["comment_2_comment"]
    
@pytest.mark.asyncio
async def test_integration_get_comment_empty_success(client, fake_comment_context):
    case_id= fake_comment_context["case_id2"]

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "INVESTIGATOR"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.post(f"/api/getComments/{case_id}")

    assert response.status_code == 200
    assert response.json()["status"] == "success"

    assert len(response.json()["comments"]) == 0
    
# - 400: invalid uuid
@pytest.mark.asyncio
async def test_integration_get_comment_missing_id_error(client, fake_comment_context):
    case_id="13"

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "INVESTIGATOR"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.post(f"/api/getComments/{case_id}")

    assert response.status_code == 400
    assert response.json()["detail"]["status"]=="error"
    assert response.json()["detail"]["message"]=="'13' is not a valid UUID format"


# - 404: Missing report id
@pytest.mark.asyncio
async def test_integration_get_comment_missing_id_error(client, fake_comment_context):
    case_id=""

    mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "INVESTIGATOR"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.post(f"/api/getComments/{case_id}")

    assert response.status_code == 404


# - 401: The JWT errors. (Missing)
@pytest.mark.asyncio
async def test_integration_get_comment_missing_cookie_error(client, fake_comment_context):
    case_id=fake_comment_context["case_id1"]

    mock_invest = ""

    client.cookies.set(COOKIE_NAME, mock_invest)

    response = client.post(f"/api/getComments/{case_id}")

    assert response.status_code == 401
    assert response.json()["detail"]["status"]=="error"
    assert response.json()["detail"]["message"]=="Not authenticated"


# - 403: The a normal user tries to get comments

@pytest.mark.asyncio
async def test_integration_get_comment_invalid_cookie_error(client, fake_comment_context):
    case_id=fake_comment_context["case_id1"]

    mock_invest = mock_invest = {
        "id": "9b74b4e3-7823-464b-a65f-4df2d75eeab3",
        "username": "TestInvest",
        "role": "USER"
    }

    client.cookies.set(COOKIE_NAME, create_token(mock_invest))

    response = client.post(f"/api/getComments/{case_id}")

    assert response.status_code == 403
    assert response.json()["detail"]["status"]=="error"
    assert response.json()["detail"]["message"]== "User unauthorized"
    


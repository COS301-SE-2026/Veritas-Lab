from fastapi import APIRouter, Header, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.core.cases import Case
from app.auth.auth import verifyJWT
from datetime import datetime
from pydantic import BaseModel
from app.core.env import ENVLoader
import asyncpg
from uuid import UUID

env = ENVLoader()

DB_USER= env.getRequiredEnv("DB_USER")
DB_PASSWORD= env.getRequiredEnv("DB_PASSWORD")
DB_HOST= env.getRequiredEnv("DB_HOST")
DB_PORT= env.getRequiredIntEnv("DB_PORT")
DB_NAME= env.getRequiredEnv("DB_NAME")

router = APIRouter(
    prefix="/api",
    tags=["Cases"]
)

class CreateCaseRequest(BaseModel):
    title: str | None = None
    description: str | None = None

class CreateSingleCaseRequest(BaseModel):
    CaseID: str | None = None

@router.post("/createCase")
async def create_case(request: CreateCaseRequest, authorization: str | None = Header(default=None)):
    try:
        payload = verifyJWT(authorization)
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": str(e)
            }
        )
    
    if payload.get("role") == "USER":
        return JSONResponse(
            status_code=403,
            content={
                "status": "error",
                "message": "User unauthorized"
            }
        )

    try:
        case = Case(CaseName=request.title, CaseCreator=payload["username"], CaseDescription=request.description)
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": str(e)
            }
        )

    case_id = await case.create()

    return JSONResponse(
        status_code=201,
        content={
            "status": "success",
            "CaseId": case_id
        }
    )

@router.post("/getCases")
async def get_cases(request:dict,authorization: str | None = Header(default=None)):
    try:
        payload = verifyJWT(authorization)
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": str(e)
            }
        )
    
    # this should not be here as any user can load the number of cases
    # if payload.get("role") == "USER":
    #     return JSONResponse(
    #         status_code=403,
    #         content={
    #             "status": "error",
    #             "message": "User unauthorized"
    #         }
    #     )
    
    connection = await asyncpg.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT
    )

    try:
        rows = await connection.fetch(
            """
            SELECT *
            FROM "Cases_DB"."Cases"
            ORDER BY casecreationdate DESC
            """
        )


        cases = []

        for row in rows:
            case = Case(
                CaseCreator=row["casecreator"],
                CaseName=row["casename"],
                CaseReviews=row["casereviews"],
                CaseDescription=row["casedescription"]
            )

            case.CaseId = row["caseid"]
            case.CaseClosed = row["caseclosed"]
            case.CaseCreationDate = row["casecreationdate"]

            cases.append(case.toJSON())

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "cases": cases
            }
        )

    finally:
        await connection.close()
    
@router.post("/getSingleCase")
async def getSingleCase(request: CreateSingleCaseRequest,authorization: str | None = Header(default=None)):
    try:
        payload = verifyJWT(authorization)
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": str(e)
            }
        )
    
    #this should not be here as any user type can clikc on one case
    # if payload.get("role") == "USER":
    #     return JSONResponse(
    #         status_code=403,
    #         content={
    #             "status": "error",
    #             "message": "User unauthorized"
    #         }
    #     )
    
    if not request.CaseID:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "CaseID required"
            }
        )

    try:
        case_id = UUID(request.CaseID)
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": str(e)
            }
        )

    connection = await asyncpg.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT
    )

    try:
        row= await connection.fetchrow(
            """
            SELECT *
            FROM "Cases_DB"."Cases"
            WHERE caseid = $1
            """,
            case_id
        )
    
        if row is None:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": "Case not found"
                }
            )

        case = Case(
            CaseCreator=row["casecreator"],
            CaseName=row["casename"],
            CaseReviews=row["casereviews"],
            CaseDescription=row["casedescription"]
        )

        case.CaseId = row["caseid"]
        case.CaseClosed = row["caseclosed"]
        case.CaseCreationDate = row["casecreationdate"]

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "case": case.toJSON()
            }
        )

    finally:
        await connection.close()


@router.post("/cases/evidence")
async def upload_evidence(case_id: str = Form(...), media: UploadFile = File(...), authorization: str | None = Header(default=None)):
    try:
        payload = verifyJWT(authorization)
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={"status": "error", "message": str(e)}
        )

    if payload.get("role") == "USER":
        return JSONResponse(
            status_code=403,
            content={"status": "error", "message": "User unauthorized"}
        )

    try:
        case_uuid = UUID(case_id)
    except ValueError as e:
        return JSONResponse(status_code=401, content={"status": "error", "message": str(e)})

    connection = await asyncpg.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT
    )

    try:
        row = await connection.fetchrow(
            """
            SELECT * FROM "Cases_DB"."Cases" WHERE caseid = $1
            """,
            case_uuid
        )

        if row is None:
            return JSONResponse(status_code=404, content={"status": "error", "message": "Case not found"})

        case = Case(
            CaseCreator=row["casecreator"],
            CaseName=row["casename"],
            CaseReviews=row["casereviews"],
            CaseDescription=row["casedescription"]
        )

        case.CaseId = row["caseid"]
        case.CaseClosed = row["caseclosed"]
        case.CaseCreationDate = row["casecreationdate"]

        result = await case.addEvidence(media, case_uuid)

        return JSONResponse(status_code=201, content={"status": "success", "evidence": result})

    finally:
        await connection.close()


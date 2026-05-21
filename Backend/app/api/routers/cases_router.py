from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.core.cases import Case
from app.auth.auth import verifyJWT
from datetime import datetime
from pydantic import BaseModel
from app.core.env import ENVLoader
import asyncpg

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
    
    if payload.get("role") == "USER":
        return JSONResponse(
            status_code=403,
            content={
                "status": "error",
                "message": "User unauthorized"
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
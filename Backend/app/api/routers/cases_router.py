from fastapi import APIRouter, Header, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.core.cases import Case
from app.auth.auth import verifyJWT
from datetime import datetime
from pydantic import BaseModel
from app.core.env import ENVLoader
import asyncpg
from uuid import UUID
import os
from urllib.parse import urlparse
from minio import Minio
from datetime import datetime, timedelta, timezone

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


def _format_case_evidence(row: dict) -> dict:
    media_id = row["mediaid"]
    media_extension = row["mediaextension"] or ""
    media_bucket = row["mediabucket"]
    media_name = row["mediatitle"]
    

    minioDomain = os.getenv("MINIO_EXTERNAL_URL") or "http://localhost:9000"
    parsedUrl = urlparse(minioDomain)
    minioEndpoint = parsedUrl.netloc if parsedUrl.netloc else minioDomain
    isSecure = parsedUrl.scheme == "https"
            #Creation of presigned URL below
    presign_client = Minio(
        minioEndpoint, # External domain the browser uses
        access_key=os.getenv("MINIO_ROOT_USER"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD"),
        region=os.getenv("AWS_REGION"),
        secure=isSecure
    )
    targetFilename = f"{media_id}{media_extension}"

    fileUrl = presign_client.presigned_get_object(
        bucket_name=media_bucket,
        object_name=targetFilename,
        expires=timedelta(hours=1)
    )

    return {
        "reportId": str(row["reportid"]),
        "mediaId": str(media_id),
        "mediaName": media_name,
        "mediaBucket": media_bucket,
        "mediaExtension": media_extension,
        "mediaTypeId": str(row["mediatypeid"]),
        "mediaUrl": fileUrl,
        "reportArtifacts": row["reportartifacts"],
        "reportFindings": row["reportfindings"],
        "reportComments": row["reportcomments"],
        "reportDateCreation": row["reportdatecreation"].isoformat() if row["reportdatecreation"] else None,
    }

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

        evidence_rows = await connection.fetch(
            """
            SELECT
                r.ReportId AS "reportid",
                r.CaseId AS "caseid",
                r.ImageId AS "mediaid",
                r.ReportArtifacts AS "reportartifacts",
                r.imagetitle AS "mediatitle",
                r.ReportFindings AS "reportfindings",
                r.ReportComments AS "reportcomments",
                r.ReportDateCreation AS "reportdatecreation",
                m.MediaTypeId AS "mediatypeid",
                m.MediaBucket AS "mediabucket",
                m.MediaExtension AS "mediaextension"
            FROM "Cases_DB"."Reports" r
            JOIN "Cases_DB"."Media" media ON r.ImageId = media.MediaId
            JOIN "Cases_DB"."MediaType" m ON media.MediaType = m.MediaTypeId
            WHERE r.CaseId = $1
            ORDER BY r.ReportDateCreation DESC
            """,
            case_id
        )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "case": case.toJSON(),
                "evidence": [_format_case_evidence(row) for row in evidence_rows]
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

    except HTTPException as e:
        # Handle 409 Conflict when image already associated with case
        if e.status_code == 409:
            return JSONResponse(status_code=409, content={"status": "error", "message": e.detail})
        # Handle 400 Bad Request for unsupported file types and malformed or scripted   
        elif e.status_code == 400:
            return JSONResponse(status_code=400, content={"status": "error", "message": e.detail})
        else:
            raise

    finally:
        await connection.close()


from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Header, Response
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from app.core.cases import Case
from app.auth.auth import verifyJWT
from app.core.env import ENVLoader
import asyncpg
from uuid import UUID
import os
from urllib.parse import urlparse
from minio import Minio
from datetime import datetime, timedelta, timezone
import uuid
from uuid import uuid4

env = ENVLoader()

DB_USER= env.getRequiredEnv("DB_USER")
DB_PASSWORD= env.getRequiredEnv("DB_PASSWORD")
DB_HOST= env.getRequiredEnv("DB_HOST")
DB_PORT= env.getRequiredIntEnv("DB_PORT")
DB_NAME= env.getRequiredEnv("DB_NAME")
DB_SSL = env.getRequiredEnv("DB_SSL").strip().lower() in ("1", "true")

async def getConnection() -> asyncpg.Connection:
    return await asyncpg.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT,
        ssl="require" if DB_SSL else None,
    )

router = APIRouter(
    prefix="/api",
    tags=["Cases"]
)

class CreateCaseRequest(BaseModel):
    title: str | None = None
    description: str | None = None

class CreateSingleCaseRequest(BaseModel):
    CaseID: str | None = None

class UpdateCommentRequest(BaseModel):
    comment: str

class CreateCommentRequest(BaseModel):
    case_id: UUID
    comment: str | None = None

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
async def create_case(case_request: CreateCaseRequest, request: Request):
    try:
        payload = verifyJWT(request)
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
        case = Case(CaseName=case_request.title, CaseCreator=payload.get("username"), CaseDescription=case_request.description)
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
async def get_cases(request: Request):
    try:
        payload = verifyJWT(request)
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": str(e)
            }
        )
    
    connection = None

    try:
        connection = await getConnection()

        if payload.get("role") == "USER":
            rows = await connection.fetch(
                """
                SELECT *
                FROM "Cases_DB"."Cases"
                WHERE caseclosed = TRUE
                ORDER BY casecreationdate DESC
                """
            )
        else:
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
    except asyncpg.PostgresError:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Database error"
            }
        )
    finally:
        if connection is not None:
            await connection.close()
    
@router.post("/getSingleCase")
async def getSingleCase(case_request: CreateSingleCaseRequest, request: Request):
    try:
        payload = verifyJWT(request)
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": str(e)
            }
        )
    
    if not case_request.CaseID:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "CaseID required"
            }
        )

    try:
        case_id = UUID(case_request.CaseID)
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": str(e)
            }
        )

    connection = None

    try:
        connection = await getConnection()

        if payload.get("role") != "USER":
            row= await connection.fetchrow(
                """
                SELECT *
                FROM "Cases_DB"."Cases"
                WHERE caseid = $1
                """,
                case_id
            )
        else:
            row= await connection.fetchrow(
                """
                SELECT *
                FROM "Cases_DB"."Cases"
                WHERE caseid = $1
                AND caseclosed = TRUE
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
                r.MediaId AS "mediaid",
                r.ReportArtifacts AS "reportartifacts",
                r.imagetitle AS "mediatitle",
                r.ReportFindings AS "reportfindings",
                r.ReportComments AS "reportcomments",
                r.ReportDateCreation AS "reportdatecreation",
                m.MediaTypeId AS "mediatypeid",
                m.MediaBucket AS "mediabucket",
                m.MediaExtension AS "mediaextension"
            FROM "Cases_DB"."Reports" r
            JOIN "Cases_DB"."Media" media ON r.MediaId = media.MediaId
            JOIN "Cases_DB"."MediaType" m ON media.MediaType = m.MediaTypeId
            WHERE r.CaseId = $1
            ORDER BY r.ReportDateCreation DESC
            """,
            case_id
        )

        return JSONResponse(
            status_code=200,
            content=jsonable_encoder({
                "status": "success",
                "case": case.toJSON(),
                "comments": await case.getComments(),
                "evidence": [_format_case_evidence(row) for row in evidence_rows]
            })
        )
    except asyncpg.PostgresError:
        return JSONResponse(
            status_code=500,
            content={
                "status":"error",
                "message":"Database error"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Internal Server Error: {type(e).__name__} - {str(e)}"
            }
        )
    finally:
        if connection is not None:
            await connection.close()


@router.post("/cases/evidence")
async def upload_evidence(request: Request, case_id: str = Form(...), media: UploadFile = File(...)):
    try:
        payload = verifyJWT(request)
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

    CaseCreator=payload["username"]

    try:
        case_uuid = UUID(case_id)
    except ValueError as e:
        return JSONResponse(status_code=401, content={"status": "error", "message": str(e)})

    connection = await getConnection()

    try:
        row = await connection.fetchrow("""
            SELECT * FROM "Cases_DB"."Cases" 
            WHERE caseid = $1 
            AND "casecreator" = $2
            AND "caseclosed" = false;
            """, 
            case_uuid,
            CaseCreator
        )
        
        if row is None:
            return JSONResponse(status_code=404, content={"status": "error", "message": "Case not found/ Nor permissions"})

        case = Case(
            CaseCreator=row["casecreator"],
            CaseName=row["casename"],
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

@router.post("/closeCase")
async def close_case(case_request: CreateSingleCaseRequest, request: Request):
    connection = None
    try:
        payload = verifyJWT(request)
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
    
    if not case_request.CaseID:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "CaseID required"
            }
        )
    
    try:
        case_uuid = UUID(case_request.CaseID)
    except ValueError as e:
        return JSONResponse(
            status_code=400, 
            content={
                "status": "error", 
                "message": "Invalid CaseID"
            }
        )

    try:    
        connection = await getConnection()

        row = await connection.fetchrow(
            """
            UPDATE "Cases_DB"."Cases"
            SET caseclosed = TRUE
            WHERE caseid = $1
            AND casecreator = $2
            RETURNING caseid
            """,
            case_uuid,
            payload.get("username")
        )

        if row is None:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": "Case not found or user unauthorized."
                }
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Case closed successfully."
            }
        )
    except asyncpg.PostgresError:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Database error"
            }
        )
    finally:
        if connection is not None:
            await connection.close()

@router.post("/editComment/case/{case_id}/comment/{comment_id}")
async def update_comment(
    case_id: str,
    comment_id: int,
    update_data: UpdateCommentRequest,
    request: Request
):
    try:
        payload = verifyJWT(request)
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={"status": "error", "message": str(e)}
        )


    try:
        case_uuid = UUID(case_id)
    except ValueError as e:
        return JSONResponse(
            status_code=400, 
            content={
                "status": "error", 
                "message": "Invalid CaseID"
            }
        )
    try:
        connection = await getConnection()

        row = await connection.fetchrow(
            """
            UPDATE "Cases_DB"."Comments"
            SET Comment = $3
            WHERE caseid = $1
            AND username = $2
            AND commentid = $4
            RETURNING commentid
            """,
            case_uuid,
            payload.get("username"),
            update_data.comment,
            comment_id
        )

        if row is None:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": "Case not found or user unauthorized."
                }
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Comment edit successfully."
            }
        )
    except asyncpg.PostgresError:
        return JSONResponse(
            status_code=500,content={
                "status": "error",
                "message": "Database error"
            }
        )

    finally:
        if connection is not None:
            await connection.close()

@router.delete("/deleteComment/comment/{comment_id}")
async def delete_comment(request: Request, comment_id: int):
    try:
        payload = verifyJWT(request)
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={"status": "error", "message": str(e)}
        )
    
    connection = None
    try:
        connection = await getConnection()

        row = await connection.fetchrow(
            """
            DELETE FROM "Cases_DB"."Comments"
            WHERE commentid = $1
            AND username = $2
            RETURNING commentid
            """,
            comment_id,
            payload.get("username")
        )

        if row is None:
            return JSONResponse(
                status_code=404,
                content={
                    "status":"error",
                    "message": "Comment not found or user unauthorized"
                }
            )
            
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Comment deleted successfully."
            }
        )
    
    except asyncpg.PostgresError:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Database error"
            }
        )
        
    finally:
        if connection is not None:
            await connection.close()

@router.post("/getComments/{case_id}")
async def retreive_comments(
    case_id: str,
    request: Request
):
    try:
        payload = verifyJWT(request)
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={"status": "error", "message": str(e)}
        )

    user_role=payload.get("role")
    if  user_role is None or user_role== "USER":
        return JSONResponse(
            status_code=403,
            content={"status": "error", "message": "User unauthorized"}
        )

    try:
        case = Case(CaseID=case_id)
        comments_data= await case.getComments()

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "comments": jsonable_encoder(comments_data)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@router.post("/delete/case/{case_id}/evidence/{media_id}")
async def delete_evidence(
    case_id:str, 
    media_id:str,
    request: Request
):
    try:
        payload = verifyJWT(request)
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={"status": "error", "message": str(e)}
        )

    user_role=payload.get("role")

    if user_role not in ["INVESTIGATOR", "ADMIN"]:
        return JSONResponse(
            status_code=403,
            content={"status": "error", "message": "User unauthorized"}
        )

    try:
        media_id = uuid.UUID(media_id)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid UUID format for media_id."}
        )
        
    try:
        case = Case(CaseID=case_id)
        username=payload.get("username") if user_role == "INVESTIGATOR" else None
        response=await case.deleteEvidence(media_id=media_id, JWT_username=username)

        return JSONResponse(
            status_code=200,
            content=response
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": f"Invalid case_id: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@router.post("/cases/comments", status_code=201)
async def create_comment(body: CreateCommentRequest, req: Request):

    try:
        payload = verifyJWT(req)
    except Exception as e:
        return JSONResponse(status_code=401,
                            content={"status": "error", "message": str(e)})

    role = payload.get("role")
    username = payload.get("username")

    if not body.comment or not Case.validateCommentLength(body.comment):
        return JSONResponse(status_code=400,
                            content={"status": "error", "message": "Comment must be a non-empty string"})

    connection = await getConnection()

    try:
        case = Case()
        case.CaseId = body.case_id

        new_comment = await case.addComment(connection, username, body.comment, role)

        return JSONResponse(status_code=201,
                            content={"status": "success", "comment": new_comment})

    except HTTPException as e:
        return JSONResponse(status_code=e.status_code,
                            content={"status": "error", "message": e.detail})

    finally:
        await connection.close()
          
@router.delete("/deleteCase")
async def delete_case(case_request: CreateSingleCaseRequest, request: Request):
    try:
        payload = verifyJWT(request)
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
    
    if not case_request.CaseID:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "CaseID required"
            }
        )
    
    try:
        case_id = uuid.UUID(case_request.CaseID)
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": str(e)
            }
        )

    try:
        result = await Case.deleteCase(
            case_id=case_id,
            username=payload.get("username"),
            role=payload.get("role")
        )

        if result["reason"] == "not_found":
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": "Case not found"
                }
            )
        
        if result["reason"] == "unauthorized":
            return JSONResponse(
                status_code=403,
                content={
                    "status": "error",
                    "message": "Only the case creator or an admin can delete this case"
                }
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Case deleted successfully"
            }
        )
    
    except asyncpg.PostgresError:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Database error"
            }
        )

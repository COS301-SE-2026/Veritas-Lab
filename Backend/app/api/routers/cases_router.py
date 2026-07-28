import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Header, Response, status, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, List
from app.core.cases import Case
from app.auth.auth import verifyJWT
from app.core.env import ENVLoader, IS_PROD
import asyncpg
from uuid import UUID
import os
from datetime import datetime, timedelta, timezone
import uuid
from uuid import uuid4
from app.core.media_relay import MediaRelay
from pathlib import Path


import boto3
from botocore.client import Config
from mypy_boto3_s3 import S3Client
env = ENVLoader()

DB_USER= env.getRequiredEnv("DB_USER")
DB_PASSWORD= env.getRequiredEnv("DB_PASSWORD")
DB_HOST= env.getRequiredEnv("DB_HOST")
DB_PORT= env.getRequiredIntEnv("DB_PORT")
DB_NAME= env.getRequiredEnv("DB_NAME")
DB_SSL = env.getRequiredEnv("DB_SSL").strip().lower() in ("1", "true")
NOT_USER= ["INVESTIGATOR", "ADMIN"]
DATABASE_ERROR_MESSAGE="Database error"
_CASE_ID_REQUIRED = "CaseID required"
_INVALID_CASE_ID = "Invalid CaseID"
_CASE_NOT_FOUND_OR_UNAUTHORIZED = "Case not found or user unauthorized."

async def getConnection() -> asyncpg.Connection:
    return await asyncpg.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT,
        ssl="require" if DB_SSL else None,
    )

def getObject(for_presign: bool = False) -> S3Client:
    if not IS_PROD:

        if for_presign:
            minio_domain = os.getenv("MINIO_EXTERNAL_URL", "http://localhost:9000")
        else:
            minio_domain = os.getenv("STORAGE_URL", "http://localhost:9000")
        
        
        if not minio_domain.startswith(("http://", "https://")):
            minio_domain = f"http://{minio_domain}"

        return boto3.client(
            "s3",
            endpoint_url=minio_domain,
            aws_access_key_id=os.getenv("MINIO_ROOT_USER"),
            aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD"),
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"}
            ),
        )

    else:
        cloud_url = os.getenv("R2_URL", "")
        
        if not cloud_url.startswith(("http://", "https://")):
            cloud_url = f"https://{cloud_url}"

        key_id=os.getenv("R2_ACCESS_KEY_ID")
        secret=os.getenv("R2_SECRET_ACCESS_KEY")
        print(f"Key ID: {repr(key_id)}")
        print(f"Secret Length: {len(secret) if secret else 'None'}")

        return boto3.client(
            "s3",
            endpoint_url=cloud_url,
            aws_access_key_id=key_id,
            aws_secret_access_key=secret,
            region_name="auto",
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"}
            ),
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

class UpdateCaseRequest(BaseModel):
    CaseID: str | None = None
    CaseName: str | None = None
    CaseDescription: str | None = None

class CreateCommentRequest(BaseModel):
    case_id: UUID
    comment: str | None = None

class SaveAnnotationsPayload(BaseModel):
    #Mapping from CamelCase to SnakeCase for Sonar to be Happy
    report_id: str = Field(..., alias="reportId")
    #since the format of the annotations was not specified by frontend we will be accepting any valid JSON
    annotations: List[Dict[str, Any]]
    model_config = ConfigDict(populate_by_name=True)

class SuccessResponse(BaseModel):
    status: str = Field(..., examples=["success"])

class ErrorResponse(BaseModel):
    status: str = Field(..., examples=["error"])
    message: str = Field(..., examples=["Invalid token or database failure"])

#A mask until the veriftJWT gets fixed to raise HTTPException so the try-excepts can be removed so FastApi can handle it 
def verify_jwt(request:Request):
    try:
        return verifyJWT(request)
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error",
                "message": str(e)
            }
        )

def verify_not_user(user_role:str):
    if  user_role not in NOT_USER: #This solves for it being blank and non sense roles.
        raise HTTPException(
            status_code=403,
            detail={
                "status": "error", 
                "message": "User unauthorized"
            }
        )

def transform_to_uuid(changer:str)->UUID:
    try:
        return UUID(changer)

    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail={"status": "error", "message": str(e)}
        )
    

def _format_case_evidence(row: dict, user : bool) -> dict:
    media_id = row["mediaid"]
    media_extension = row["mediaextension"] or ""
    media_bucket = row["mediabucket"]
    media_name = row["mediatitle"]

    
            #Creation of presigned URL below
    target_filename = f"{media_id}{media_extension}"
    if user: # so none user log in block
        presign_client =  getObject(for_presign=True)

        file_url = presign_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket':media_bucket,
                'Key': target_filename
            },
            ExpiresIn=3600 # An hour 
        )
    else:
        # user block: It needs the  url to be empty to hide the actual image since it could be sensitive info.
        file_url= ""

    return {
        "reportId": str(row["reportid"]),
        "mediaId": str(media_id),
        "mediaName": media_name,
        "mediaBucket": media_bucket,
        "mediaExtension": media_extension,
        "mediaTypeId": str(row["mediatypeid"]),
        "mediaUrl": file_url,
        "annotations": json.loads(row["annotations"]) if isinstance(row["annotations"], str) else (row["annotations"] or []),
        "reportArtifacts": json.loads(row["reportartifacts"]) if isinstance(row["reportartifacts"], str) else row["reportartifacts"],
        "reportFindings": row["reportfindings"],
        "reportComments": row["reportcomments"],
        "reportDateCreation": row["reportdatecreation"].isoformat() if row["reportdatecreation"] else None,
    }

@router.post(
    "/createCase",
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - User unauthorized"
        },
    }
)
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
    verify_not_user(payload.get("role"))

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

@router.post(
    "/getCases",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized - Invalid or missing token"},
        500: {"model": ErrorResponse, "description": "Internal Server Error - Database error"},
    }
)
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
                "message": DATABASE_ERROR_MESSAGE
            }
        )
    finally:
        if connection is not None:
            await connection.close()
    
@router.post(
    "/getSingleCase",
    responses={
        500: {
            "model": ErrorResponse,
            "description": DATABASE_ERROR_MESSAGE
        },
        401: {
            "model": ErrorResponse,
            "description": "Unauthorized - Missing or invalid JWT token",
        },
        404:{
            "model": ErrorResponse,
            "description": " Case not found"
        },
        400:{
            "model": ErrorResponse,
            "description": _CASE_ID_REQUIRED
        }

    }
)
async def get_single_case(case_request: CreateSingleCaseRequest, request: Request):
    try:
        payload = verify_jwt(request)
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": str(e)
            }
        )
    
    if not case_request.CaseID:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": _CASE_ID_REQUIRED
            }
        )

    try:
        case_id = UUID(case_request.CaseID)
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error",
                "message": str(e)
            }
        )

    connection = None
    is_user= None
    try:
        connection = await getConnection()
        is_user = payload.get("role") != "USER"
        if is_user:
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
            raise HTTPException(
                status_code=404,
                detail={
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
                m.MediaExtension AS "mediaextension",
                media.MediaAnnotations AS "annotations"
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
                "evidence": [_format_case_evidence(row,is_user) for row in evidence_rows]
            })
        )
    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status":"error",
                "message":DATABASE_ERROR_MESSAGE
            }
        )
    except HTTPException:
        raise #so the dumb Exception doesn't override the error message
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


@router.post(
    "/cases/evidence",
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Unauthorized - Missing or invalid JWT token",
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - User lacks required investigator/admin permissions",
        },
        404: {
            "model": ErrorResponse,
            "description": "Case not found or user lacks permission",
        },
    },
)
async def upload_evidence(request: Request, background_task: BackgroundTasks, case_id: str = Form(...), media: UploadFile = File(...)):

    payload = verify_jwt(request)


    verify_not_user(payload.get("role"))

    CaseCreator=payload["username"]

    try:
        case_uuid = UUID(case_id)
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={
                "status": "error", 
                "message": str(e)
            }
        )

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

        # start pipeline here
        extension = Path(result["Filename"]).suffix.lower()
        media_id = UUID(result["MediaId"])

        media_relay = MediaRelay(media_id=media_id, extension=extension)

        background_task.add_task(media_relay.relay_to_service)

        return JSONResponse(status_code=201, content={"status": "success", "evidence": result})

    except HTTPException as e:
        raise

    finally:
        await connection.close()

@router.post("/closeCase",
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - User unauthorized"},
    }
)
async def close_case(case_request: CreateSingleCaseRequest, request: Request):
    connection = None
    try:
        payload = verifyJWT(request)
    except ValueError as e:
        return JSONResponse(
            status_code=401,
            content={"status": "error", "message": str(e)}
        )

    verify_not_user(payload.get("role"))
    
    if not case_request.CaseID:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": _CASE_ID_REQUIRED
            }
        )
    
    try:
        case_uuid = UUID(case_request.CaseID)
    except ValueError as e:
        return JSONResponse(
            status_code=400, 
            content={
                "status": "error", 
                "message": _INVALID_CASE_ID
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
                    "message": _CASE_NOT_FOUND_OR_UNAUTHORIZED
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
                "message": DATABASE_ERROR_MESSAGE
            }
        )
    finally:
        if connection is not None:
            await connection.close()

@router.post("/updateCase")
async def update_case(case_request: UpdateCaseRequest, request: Request):
    connection = None
    try:
        payload = verifyJWT(request)
    except ValueError as e:
        return JSONResponse(status_code=401, content={"status": "error", "message": str(e)})

    verify_not_user(payload.get("role"))

    if not case_request.CaseID:
        return JSONResponse(status_code=400, content={"status": "error", "message": _CASE_ID_REQUIRED})

    try:
        case_uuid = UUID(case_request.CaseID)
    except ValueError:
        return JSONResponse(status_code=400, content={"status": "error", "message": _INVALID_CASE_ID})

    if case_request.CaseName is None and case_request.CaseDescription is None:
        return JSONResponse(status_code=400, content={"status": "error", "message": "At least one of CaseName or CaseDescription must be provided"})

    validated_name = None
    if case_request.CaseName is not None:
        try:
            validated_name = Case(CaseName=case_request.CaseName).CaseName  # This will raise ValueError if invalid
        except ValueError as e:
            return JSONResponse(status_code=400, content={"status": "error", "message": str(e)})

    try:
        connection = await getConnection()

        row = await connection.fetchrow(
            """
            UPDATE "Cases_DB"."Cases"
            set casename = COALESCE($3, casename),
                casedescription = COALESCE($4, casedescription)
            WHERE caseid = $1
            AND casecreator = $2
            RETURNING caseid
            """,
            case_uuid,
            payload.get("username"),
            validated_name,
            case_request.CaseDescription
        )

        if row is None:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": _CASE_NOT_FOUND_OR_UNAUTHORIZED
                }
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Case updated successfully."
            }
        )

    except asyncpg.PostgresError:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
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
                "message": _INVALID_CASE_ID
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
                    "message": _CASE_NOT_FOUND_OR_UNAUTHORIZED
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
                "message": DATABASE_ERROR_MESSAGE
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
                "message": DATABASE_ERROR_MESSAGE
            }
        )
        
    finally:
        if connection is not None:
            await connection.close()

@router.post(
    "/getComments/{case_id}",
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - User unauthorized"},
    }
)
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
    verify_not_user(user_role) 

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

@router.post(
    "/delete/case/{case_id}/evidence/{media_id}",
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - User unauthorized"},
    }
)
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

    verify_not_user(user_role)

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
        case = Case(CaseID=str(body.case_id))

        new_comment = await case.addComment(connection, username, body.comment, role)

        return JSONResponse(status_code=201,
                            content={"status": "success", "comment": new_comment})

    finally:
        await connection.close()
          
@router.delete(
    "/deleteCase",
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - User unauthorized"},
    }
)
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
    
    verify_not_user(payload.get("role"))
    
    if not case_request.CaseID:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": _CASE_ID_REQUIRED
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
                "message": DATABASE_ERROR_MESSAGE
            }
        )

async def _save_annotations(report_id:UUID,annotations:str,user_name:str):
    #This not in a class cases because it is faster to use the reportId in a query then to use the caseId and EvidenceId
    query = """
        UPDATE "Cases_DB"."Media" m
        SET MediaAnnotations = $1::jsonb
        FROM "Cases_DB"."Reports" r 
        INNER JOIN "Cases_DB"."Cases" c ON r.CaseId = c.CaseId
        WHERE m.MediaId = r.MediaId
          AND c.CaseCreator = $3 
          AND r.ReportId = $2;
    """
    con = None
    try:
        con=await getConnection()
        await con.execute(query, annotations, report_id, user_name)
    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
            }
        )

    finally:
        if con:
            await con.close()

@router.post("/saveAnnotations", 
    status_code=status.HTTP_200_OK,
    summary="Save Report Annotations",
    description="Updates the JSONB media annotations for a specific report/evidence item in PostgreSQL.",
    response_model=SuccessResponse,
    responses={
        200: {
            "description": "Annotations successfully saved.",
            "model": SuccessResponse,
            "content": {
                "application/json": {
                    "example": {"status": "success"}
                }
            },
        },
        401: {
            "description": "Unauthorized - Missing/Invalid JWT cookie or non-UUID report ID format.",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "Invalid JWT": {
                            "summary": "Invalid JWT Token",
                            "value": {"status": "error", "message": "Signature has expired."}
                        },
                        "Invalid UUID": {
                            "summary": "Invalid Report UUID",
                            "value": {"status": "error", "message": "badly formed hexadecimal UUID string"}
                        }
                    }
                }
            },
        },
        403: {
            "description": "Forbidden - User does not have permission (e.g. Standard 'USER' role).",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"status": "error", "message": "User unauthorized"}
                }
            },
        },
        500: {
            "description": "Internal Server Error - Database failure or unhandled exception.",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "Database Error": {
                            "summary": "Database Failure",
                            "value": {"detail": {"status": "error", "message": "Database error"}}
                        },
                        "Server Exception": {
                            "summary": "Unexpected Error",
                            "value": {"detail": {"status": "error", "message": "An unexpected error occurred"}}
                        }
                    }
                }
            },
        },
    }
)
async def save_annotations(payload: SaveAnnotationsPayload, request:Request):
    cookie=verify_jwt(request)
    user_role=cookie.get("role")
    # Checking authorization
    verify_not_user(user_role)
    user_name=cookie.get("username")

    try:
        report_id=transform_to_uuid(payload.report_id)
        annotations_json_str = json.dumps(payload.annotations)
        await _save_annotations(report_id,annotations_json_str,user_name)

        return JSONResponse(
            status_code=200,
            content={
                "status": "success"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": str(e)}
        ) 

    
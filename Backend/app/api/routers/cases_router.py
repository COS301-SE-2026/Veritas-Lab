import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Header, Response, status, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import APIKeyCookie
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, List, Annotated
from app.core.cases import (
    Case,
    CASE_NOT_FOUND,
    MISSING_CASE_ID,
    PDF_SCRIPTS_NOT_ALLOWED,
    UNSUPPORTED_EXTENSION_PREFIX,
    MEDIA_ALREADY_ON_CASE,
    INTERNAL_SERVER_ERROR_STORAGE,
)
from app.auth.auth import verify_jwt, COOKIE_NAME, NOT_AUTH, EXPIRED_TOKEN, INVALID_TOKEN, INVALID_TOKEN_401
import asyncpg
from uuid import UUID
from datetime import datetime, timedelta, timezone
import uuid
from uuid import uuid4
from app.core.media_relay import MediaRelay
from pathlib import Path
import boto3
from botocore.client import Config
from mypy_boto3_s3 import S3Client
from app.core.env import Postgres_Settings, Minio_Settings, Other_Settings, R2_Settings
from app.core.cases import get_object
from app.core.database import get_connection

postgres_settings = Postgres_Settings()
other_settings = Other_Settings()
r2_settings = R2_Settings()
minio_settings = Minio_Settings()

NOT_USER= ["INVESTIGATOR", "ADMIN"]
DATABASE_ERROR_MESSAGE="Database error"
CASE_ID_REQUIRED = "CaseID required"
INVALID_CASE_ID = "Invalid CaseID"
CASE_NOT_FOUND_OR_UNAUTHORIZED = "Case not found or user unauthorized."
COOKIE_SCHEME=APIKeyCookie(name=COOKIE_NAME, auto_error=False)
USER_UNAUTHORIZED = "User unauthorized"
CASE_UPDATED_SUCCESS = "Case updated successfully."
UPDATE_FIELDS_REQUIRED = "At least one of CaseName or CaseDescription must be provided"
COMMENT_UPDATED_SUCCESS = "Comment edit successfully."


UPDATE_CASE_SQL = """
    UPDATE "Cases_DB"."Cases"
    SET casename = COALESCE($3, casename),
        casedescription = COALESCE($4, casedescription)
    WHERE caseid = $1
        AND casecreator = $2
    RETURNING caseid
    """

USER_UNAUTHORIZED_403 = {
            "description": "Forbidden - User unauthorized",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": "User unauthorized"
                        }
                    }
                }
            }
        }

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

class create_comment_request(BaseModel):
    case_id: UUID
    comment: str | None = None

class save_snnotations_payload(BaseModel):
    #Mapping from CamelCase to SnakeCase for Sonar to be Happy
    connector_id: str = Field(..., alias="reportId")
    #since the format of the annotations was not specified by frontend we will be accepting any valid JSON
    annotations: List[Dict[str, Any]]
    model_config = ConfigDict(populate_by_name=True)

class success_response(BaseModel):
    status: str = Field(..., examples=["success"])

class error_response(BaseModel):
    status: str = Field(..., examples=["error"])
    message: str = Field(..., examples=["Invalid token or database failure"])
  

def verify_not_user(user_role:str):
    if  user_role  not in NOT_USER: #This solves for it being blank and non sense roles.
        raise HTTPException(
            status_code=403,
            detail={
                "status": "error", 
                "message": USER_UNAUTHORIZED
            }
        )

def transform_to_uuid(changer:str)->UUID:
    try:
        return UUID(changer)

    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error", 
                "message": str(e)
            }
        )

def media_id_valid_uuid(media_id)->UUID:
    try:
        return UUID(media_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error", 
                "message": "Media is an invalid uuid"
            }
        )
    

def _row_to_case(row: dict) -> Case:
    case = Case(
        case_creator=row["casecreator"],
        case_name=row["casename"],
        case_description=row["casedescription"]
    )

    case.case_id = row["caseid"]
    case.case_closed = row["caseclosed"]
    case.case_creation_date = row["casecreationdate"]

    return case

def _format_case_evidence(row: dict, user : bool) -> dict:
    media_id = row["mediaid"]
    media_extension = row["mediaextension"] or ""
    media_bucket = row["mediabucket"]
    media_name = row["mediatitle"]

    
            #Creation of presigned URL below
    target_filename = f"{media_id}{media_extension}"
    if user: # so none user log in block
        presign_client =  get_object(for_presign=True)

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
        "reportCertainty": row["reportcertainty"],
        "reportDateCreation": row["reportdatecreation"].isoformat() if row["reportdatecreation"] else None,
    }

@router.post(
    "/createCase",
    summary="Create a Case",
    status_code=201,
    dependencies=[Depends(COOKIE_SCHEME)],
    description="Creates a new case for an authenticated user. Those with the role 'USER' cannot use this endpoint.",
    responses={
        201: {
            "description": "Case created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "CaseId": "550e8400-e29b-41d4-a716-676767676767"
                    }
                }
            }
        },

        400: {
            "description": "Bad Request - Invalid case data",
            "content": {
                "application/json": {
                    "examples": {
                        "MissingCaseName": {
                            "summary": "Missing case name",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "CaseName is required"
                                }
                            }
                        },
                        "CaseNameTooLong": {
                            "summary": "Case name too long",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "CaseName must be 255 characters or less"
                                }
                            }
                        }
                    }
                }
            }
        },

        401: INVALID_TOKEN_401,

        403: USER_UNAUTHORIZED_403,

        409: {
            "description": "Conflict - Case already exists",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": "This case already exists"
                        }
                    }
                }
            }
        }
    }
)
async def create_case(case_request: CreateCaseRequest, request: Request):
    payload = verify_jwt(request)
    verify_not_user(payload.get("role"))

    try:
        case = Case(
            case_name=case_request.title, 
            case_creator=payload.get("username"), 
            case_description=case_request.description
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": str(e)
            }
        )

    case_id = await case.create()

    return {
        "status": "success",
        "CaseId": case_id
    }

@router.post(
    "/getCases",
    dependencies=[Depends(COOKIE_SCHEME)],
    status_code=status.HTTP_200_OK,
    summary='List Cases',
    description=(
        "Returns cases visible to the caller. INVESTIGATOR and ADMIN see every case. "
        "USER role sees only closed cases."
    ),
    responses={
        200: {
            "description": "Cases retrieved successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "cases": [
                            {
                                "caseId": "12345678-abcd-ef01-2345-6789abcdef01",
                                "caseName": "Reciepts sus",
                                "caseDescription": "Sus receipts case",
                                "caseClosed": False,
                                "caseCreationDate": "2026-05-20T19:43:02+00:00",
                            }
                        ]
                    }
                }
            }
        },

        401: {
            "model": error_response,
            "description": "Unauthorized - JWT errors (missing, invalid, or expired)",
            "content": {
                "application/json": {
                    "examples": {
                        "Expired JWT": {
                            "summary": "JWT Token Expired",
                            "value": {
                                "detail":{
                                    "status": "error",
                                    "message": "Token has expired"
                                }
                            }
                        },
                        "No authorization": {
                            "summary": "Missing JWT Cookie or Header",
                            "value": {
                                "detail":{
                                    "status": "error",
                                    "message": "Not authenticated"
                                }
                            }
                        },
                        "Invalid token": {
                            "summary": "Invalid JWT Signature/Malformed",
                            "value": {
                                "detail":{
                                    "status": "error",
                                    "message": "Invalid token"
                                }
                            }
                        }
                    }
                }
            }
        },

        500: {
            "model": error_response,
            "description": "Internal server error " + DATABASE_ERROR_MESSAGE,
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": DATABASE_ERROR_MESSAGE
                        }
                    }
                }
            }
        }
    }
)
async def get_cases(request: Request, connection: asyncpg.Connection = Depends(get_connection)):
  
    payload = verify_jwt(request)

    try:
        is_standard_user = payload.get("role") == "USER"

        rows = await connection.fetch(
            """
            SELECT caseid, casecreator, casename, casedescription, caseclosed, casecreationdate
            FROM "Cases_DB"."Cases"
            WHERE $1::boolean IS FALSE OR caseclosed IS TRUE
            ORDER BY casecreationdate DESC
            """,
            is_standard_user
        )

        return {
            "status": "success",
            "cases": [jsonable_encoder(_row_to_case(row).to_json()) for row in rows]
        }

    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
            }
        )

    
@router.post(
    "/getSingleCase",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Get a single case",
    description=(
        "Returns one case with its comments and evidence. INVESTIGATOR and ADMIN can "
        "get any case and receive presigned media URLs. The USER role can only "
        "get closed cases, and their evidence is returned with an empty mediaUrl."
    ),
    responses={
        200: {
            "description": "Case retrieved successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "case":{
                            "caseId": "12345678-abcd-ef01-2345-6789abcdef01",
                            "caseName": "Flood in Westville",
                            "caseCreator": "investigator_user",
                            "caseDescription": "Flood investigation case",
                            "caseClosed": False,
                            "caseCreationDate": "2026-05-20T19:43:02+00:00"
                        },
                        "comments": [],
                        "evidence": []
                    }
                }
            }
        },
        400: {
            "model": error_response,
            "description": "Bad Request - Missing or malformed CaseID",
            "content": {
                "application/json": {
                    "examples": {
                        "Missing CaseID": {
                            "summary": "No CaseID supplied",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": CASE_ID_REQUIRED
                                }
                            }
                        },
                        "Invalid CaseID": {
                            "summary": "CaseID is not a valid UUID",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "'not-a-valid-uuid' is not a valid UUID format"
                                }
                            }
                        }
                    }
                }
            }
        },
        401: INVALID_TOKEN_401,
        404: {
            "model": error_response,
            "description": "Not Found - Case does not exist or USER requested on open case.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": CASE_NOT_FOUND
                        }
                    }
                }
            }
        },
        500: {
            "model": error_response,
            "description": "Internal Server Error - " + DATABASE_ERROR_MESSAGE,
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": DATABASE_ERROR_MESSAGE
                        }
                    }
                }
            }
        }
    }
)
async def get_single_case(case_request: CreateSingleCaseRequest, request: Request, connection: asyncpg.Connection = Depends(get_connection)):
    payload = verify_jwt(request)

    if not case_request.CaseID:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": CASE_ID_REQUIRED
            }
        )

    case_id = Case(case_id=case_request.CaseID).case_id

    try:
        is_standard_user = payload.get("role") == "USER"

        row = await connection.fetchrow(
            """
            SELECT caseid, casecreator, casename, casedescription, caseclosed, casecreationdate
            FROM "Cases_DB"."Cases"
            WHERE caseid = $1
                AND ($2::boolean IS FALSE OR caseclosed IS TRUE)
            """,
            case_id,
            is_standard_user
        )

        if row is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": CASE_NOT_FOUND
                }
            )

        case = _row_to_case(row)

        evidence_rows = await connection.fetch(
             """
            SELECT
                r.ReportID AS "reportid",
                r.CaseID AS "caseid",
                r.MediaID AS "mediaid",
                r.ReportArtifacts AS "reportartifacts",
                r.imagetitle AS "mediatitle",
                r.ReportFindings AS "reportfindings",
                r.ReportComments AS "reportcomments",
                r.ReportCertainty AS "reportcertainty",
                r.ReportDateCreation AS "reportdatecreation",
                m.MediatypeId AS "mediatypeid",
                m.MediaExtension AS "mediaextension",
                m.MediaBucket AS "mediabucket",
                media.MediaAnnotations AS "annotations"
            FROM "Cases_DB"."Reports" r
            JOIN "Cases_DB"."Media" media ON r.MediaID = media.MediaID
            JOIN "Cases_DB"."MediaType" m ON media.MediaType = m.MediaTypeId
            WHERE r.CaseID = $1
            ORDER BY r.ReportDateCreation DESC
            """,
            case_id,
        )

        return jsonable_encoder({
            "status": "success",
            "case": case.to_json(),
            "comments": await case.get_comments(),
            "evidence": [
                _format_case_evidence(evidence_row, not is_standard_user)
                for evidence_row in evidence_rows
            ]
        })

    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
            }
        )

 

@router.post(
    "/cases/evidence",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Upload case evidence",
    description=(
        "Uploads a media file as evidence against an open case. Only the "
        "INVESTIGATOR or ADMIN who created the case may upload to it. The file is "
        "stored in object storage and queued for AI analysis."
    ),
    responses={
        201: {
            "description": "Evidence uploaded successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "evidence": {
                            "MediaId": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                            "Filename": "evidence.png",
                            "url": "https://localhost:9000/images/aaaaaaaa.png",
                            "Status": "uploaded"
                        }
                    }
                }
            }
        },
        400: {
            "model": error_response,
            "description": "Bad Request - malformed case id, unsupported file, or unsafe PDF.",
            "content": {
                "application/json": {
                    "examples": {
                        "Invalid Case UUID": {
                            "summary": "case_id is not a valid UUID",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "'fake-uuid' is not a valid UUID format"
                                }
                            }
                        },
                        "Unsupported extension": {
                            "summary": "File type not allowed",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": f"{UNSUPPORTED_EXTENSION_PREFIX}.exe"
                                }
                            }
                        },
                        "Unsafe PDF": {
                            "summary": "PDF contains scripts",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": PDF_SCRIPTS_NOT_ALLOWED
                                }
                            }
                        }
                    }
                }
            }
        },
        401: INVALID_TOKEN_401,
        403: USER_UNAUTHORIZED_403,
        404: {
            "model": error_response,
            "description": "Not Found - no open case with that id created by this user.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": CASE_NOT_FOUND_OR_UNAUTHORIZED
                        }
                    }
                }
            }
        },
        409: {
            "model": error_response,
            "description": "Conflict - this media is already attached to the case.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": MEDIA_ALREADY_ON_CASE
                        }
                    }
                }
            }
        },
        500: {
            "model": error_response,
            "description": (
                "Internal Server Error - " + DATABASE_ERROR_MESSAGE
                + " or object storage could not be reached."
            ),
            "content": {
                "application/json": {
                    "examples": {
                        "Database error": {
                            "summary": "Database failure",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": DATABASE_ERROR_MESSAGE
                                }
                            }
                        },
                        "Storage unavailable": {
                            "summary": "Object storage could not be reached",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": INTERNAL_SERVER_ERROR_STORAGE
                                }
                            }
                        }
                    }
                }
            }
        }
    },
)
async def upload_evidence(
    request: Request,
    background_task: BackgroundTasks,
    case_id: Annotated[str, Form()],
    media: Annotated[UploadFile, File()],
    connection: asyncpg.Connection = Depends(get_connection)
):
    payload = verify_jwt(request)

    verify_not_user(payload.get("role"))

    case_creator = payload["username"]

    # Case.__init__ validates the UUID and raises a 400 on a malformed value
    validated_case_id = Case(case_id=case_id).case_id

    try:
        row = await connection.fetchrow(
            """
            SELECT caseid, casecreator, casename, casedescription, caseclosed, casecreationdate
            FROM "Cases_DB"."Cases"
            WHERE caseid = $1
                AND casecreator = $2
                AND caseclosed = FALSE
            """,
            validated_case_id,
            case_creator
        )

        if row is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error", 
                    "message": CASE_NOT_FOUND_OR_UNAUTHORIZED
                }
            )

        case = _row_to_case(row)

        result = await case.add_evidence(media, validated_case_id)

        # start the media pipeline
        extension = Path(result["Filename"]).suffix.lower()
        media_id = UUID(result["MediaId"])

        media_relay = MediaRelay(media_id=media_id, extension=extension)
        background_task.add_task(media_relay.relay_to_service)

        return {
            "status": "success",
            "evidence": result
        }

    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
            }
        )

@router.post(
    "/closeCase",
    summary="Close a case",
    status_code=200,
    dependencies=[Depends(COOKIE_SCHEME)],
    description="The creator of a case can close the case.",
    responses={
        200: {
            "description": "Case closed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Case closed successfully."
                    }
                }
            }
        },

        400: {
            "description": "Bad Request - Invalid case ID",
            "content": {
                "application/json": {
                    "examples": {
                        "MissingCaseID": {
                            "summary": "Missing case ID",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": CASE_ID_REQUIRED
                                }
                            }
                        },

                        "InvalidCaseID": {
                            "summary": "Invalid case ID",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": INVALID_CASE_ID
                                }
                            }
                        }
                    }
                }
            }
        },

        401: INVALID_TOKEN_401,

        403: USER_UNAUTHORIZED_403,

        404: {
            "description": "Case not found or user unauthorized",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": CASE_NOT_FOUND_OR_UNAUTHORIZED
                        }
                    }
                }
            }
        },

        500: {
            "description": "Database error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": DATABASE_ERROR_MESSAGE
                        }
                    }
                }
            }
        }
    }
)
async def close_case(
    case_request: CreateSingleCaseRequest,
    request: Request,
    connection: asyncpg.Connection = Depends(get_connection)
):
    payload = verify_jwt(request)

    verify_not_user(payload.get("role"))
    
    if not case_request.CaseID:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": CASE_ID_REQUIRED
            }
        )
    
    try:
        case_uuid = UUID(case_request.CaseID)
    except ValueError as e:
        raise HTTPException(
            status_code=400, 
            detail={
                "status": "error", 
                "message": INVALID_CASE_ID
            }
        )

    try:    
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
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": CASE_NOT_FOUND_OR_UNAUTHORIZED
                }
            )

        return {
            "status": "success",
            "message": "Case closed successfully."
        }
    
    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
            }
        )
@router.post(
    "/updateCase",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Update a Case",
    description=(
        "Updates the name and/or the description of a case. Only INVESTIGATOR and "
        "ADMIN roles may call this endpoint, and a case can only be updated by the "
        "user who created it. Fields that are omitted are left unchanged, so either "
        "CaseName or CaseDescription must be supplied."
    ),
    responses={
        200: {
            "description": "Case updated successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": CASE_UPDATED_SUCCESS
                    }
                }
            }
        },

        400: {
            "model": error_response,
            "description": "Bad Request - Missing/malformed CaseID or invalid update fields",
            "content": {
                "application/json": {
                    "examples": {
                        "Missing CaseID": {
                            "summary": "No CaseID supplied",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": CASE_ID_REQUIRED
                                }
                            }
                        },
                        "Invalid CaseID": {
                            "summary": "CaseID is not a valid UUID",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "'not-a-valid-uuid' is not a valid UUID format"
                                }
                            }
                        },
                        "No fields": {
                            "summary": "Neither CaseName nor CaseDescription supplied",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": UPDATE_FIELDS_REQUIRED
                                }
                            }
                        },
                        "Blank CaseName": {
                            "summary": "CaseName is empty or whitespace",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "CaseName is required"
                                }
                            }
                        },
                        "CaseName too long": {
                            "summary": "CaseName exceeds 255 characters",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "CaseName must be 255 characters or less"
                                }
                            }
                        }
                    }
                }
            }
        },

        401: INVALID_TOKEN_401,

        403: USER_UNAUTHORIZED_403,

        404: {
            "model": error_response,
            "description": "Not Found - Case does not exist or the caller is not its creator",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": CASE_NOT_FOUND_OR_UNAUTHORIZED
                        }
                    }
                }
            }
        },

        500: {
            "model": error_response,
            "description": "Internal Server Error - " + DATABASE_ERROR_MESSAGE,
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": DATABASE_ERROR_MESSAGE
                        }
                    }
                }
            }
        }
    }
)
async def update_case(
    case_request: UpdateCaseRequest,
    request: Request,
    connection: asyncpg.Connection = Depends(get_connection)
):
    payload = verify_jwt(request)

    verify_not_user(payload.get("role"))

    if not case_request.CaseID:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": CASE_ID_REQUIRED
            }
        )

    case_id = Case(case_id=case_request.CaseID).case_id

    if case_request.CaseName is None and case_request.CaseDescription is None:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": UPDATE_FIELDS_REQUIRED
            }
        )

    validated_name = None

    if case_request.CaseName is not None:
        try:
            validated_name = Case(case_name=case_request.CaseName).case_name
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": str(e)
                }
            )

    try:
        row = await connection.fetchrow(
            """
            UPDATE "Cases_DB"."Cases"
            SET casename = COALESCE($3, casename),
                casedescription = COALESCE($4, casedescription)
            WHERE caseid = $1
                AND casecreator = $2
            RETURNING caseid
            """,
            case_id,
            payload.get("username"),
            validated_name,
            case_request.CaseDescription
        )

        if row is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": CASE_NOT_FOUND_OR_UNAUTHORIZED
                }
            )

        return {
            "status": "success",
            "message": CASE_UPDATED_SUCCESS 
        }

    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
            }
        )

@router.post(
    "/editComment/case/{case_id}/comment/{comment_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Edit a Comment",
    description=(
        "Edits the text of a comment. Any authenticated role may call this endpoint, "
        "but a comment can only be edited by the user who wrote it, on the case it "
        "was written on."
    ),
    responses={
        200: {
            "description": "Comment updated successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": COMMENT_UPDATED_SUCCESS
                    }
                }
            }
        },

        400: {
            "model": error_response,
            "description": "Bad Request - Malformed CaseID",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": "'not-a-valid-uuid' is not a valid UUID format"
                        }
                    }
                }
            }
        },

        401: INVALID_TOKEN_401,

        404: {
            "model": error_response,
            "description": (
                "Not Found - The comment does not exist, is not on this case, "
                "or was not written by the caller."
            ),
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": CASE_NOT_FOUND_OR_UNAUTHORIZED
                        }
                    }
                }
            }
        },

        500: {
            "model": error_response,
            "description": "Internal Server Error - " + DATABASE_ERROR_MESSAGE,
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": DATABASE_ERROR_MESSAGE
                        }
                    }
                }
            }
        }
    },
)
async def update_comment(
    case_id: str,
    comment_id: int,
    update_data: UpdateCommentRequest,
    request: Request,
    connection: asyncpg.Connection = Depends(get_connection)
):
    payload = verify_jwt(request)

    case_uuid = Case(case_id=case_id).case_id

    try:
        row = await connection.fetchrow(
            """
            UPDATE "Cases_DB"."Comments"
            SET comment = $3
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
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": CASE_NOT_FOUND_OR_UNAUTHORIZED
                }
            )

        return {
            "status": "success",
            "message": COMMENT_UPDATED_SUCCESS
        }

    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
            }
        )

@router.delete(
    "/deleteComment/comment/{comment_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Delete comment",
    description="An authenticated user is able to delete their own comment.",
    responses={
        200: {
            "description": "Comment deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Comment deleted successfully."
                    }
                }
            }
        },

        401: INVALID_TOKEN_401,
        404: {
            "description": "Comment could not be deleted",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": "Comment not found or user unauthorized"
                        }
                    }
                }
            }
        },

        500: {
            "description": "Comment could not be deleted",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": DATABASE_ERROR_MESSAGE
                        }
                    }
                }
            }
        }
    }
)
async def delete_comment(
    request: Request,
    comment_id: int,
    connection: asyncpg.Connection = Depends(get_connection)
):
    payload = verify_jwt(request)
    username = payload.get("username")
    
    try:
        row = await connection.fetchrow(
            """
            DELETE FROM "Cases_DB"."Comments"
            WHERE commentid = $1
            AND username = $2
            RETURNING commentid
            """,
            comment_id,
            username
        )

        if row is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "status":"error",
                    "message": "Comment not found or user unauthorized"
                }
            )
            
        return {
            "status": "success",
            "message": "Comment deleted successfully."
        }
    
    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
            }
        )
        
@router.post(
    "/getComments/{case_id}",
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Retrieve comments",
    description="Fetches comments for a specific case.",
    responses={
        200: {
            "description": "Retrieval of comments was successful.",
            "model": success_response,
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "comments": [
                            {
                                "commentid": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
                                "username": "TestInvestigator",
                                "comment": "Reviewed section 3. Everything looks consistent with the report.",
                                "commenttimestamp": "2026-08-10T14:30:00Z"
                            },
                            {
                                "commentid": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                                "username": "LeadAnalyst",
                                "comment": "Additional context required for media hash verification.",
                                "commenttimestamp": "2026-08-10T15:15:00Z"
                            }
                        ]
                    }
                }
            },
        },
        404: {
            "description": "Not found - Missing case Id"
        },
        400: {
            "description": "Bad request- Poorly formatted UUID",
            "content": {
                "application/json": {
                    "example": {
                        "detail":{
                            "status": "error",
                            "message": "fake-uuid is not a valid UUID format"
                        }
                    }
                }
            }
        },
        401: INVALID_TOKEN_401,
        403: {
            "description": "Forbidden - User lacks sufficient permissions",
            "content": {
                "application/json": {
                    "example": {
                        "detail":{
                            "status": "error",
                            "message": "User unauthorized"
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error - Database connection or unexpected server failure",
            "content": {
                "application/json": {
                    "examples": {
                        "Database Error": {
                            "summary": "PostgreSQL Exception",
                            "value": {
                                "detail": "Database connection failure. Internal Server Error."
                            }
                        },
                        "Unhandled Exception": {
                            "summary": "General Server Failure",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "An unexpected error occurred."
                                }
                            }
                        }
                    }
                }
            }
        }
    }
)
async def retreive_comments(
    case_id: str,
    request: Request
):

    payload = verify_jwt(request)
    user_role=payload.get("role")
    verify_not_user(user_role) 

    try:
        case = Case(case_id=case_id)
        comments_data= await case.get_comments()

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
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error", 
                "message": str(e)
            }
        )


@router.post(
    "/delete/case/{case_id}/evidence/{media_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Delete case evidence",
    description="Deletes a specific evidence item/media attached to a case. Investigators can only delete evidence from cases they created, while Admins can delete any evidence.",
    responses={
        200: {
            "description": "Evidence deleted successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "deleted": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Invalid UUID format or missing ID.",
            "content": {
                "application/json": {
                    "examples": {
                        "Invalid Media UUID": {
                            "summary": "Invalid Media ID format",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Media is an invalid uuid"
                                }
                            }
                        },
                        "Invalid Case UUID": {
                            "summary": "Invalid Case ID format",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "'fake-uuid' is not a valid UUID format"
                                }
                            }
                        }
                    }
                }
            }
        },
        401: INVALID_TOKEN_401,
        403: {
            "description": "Forbidden - User lacks permission or is standard USER role.",
            "content": {
                "application/json": {
                    "examples": {
                        "Role Forbidden": {
                            "summary": "Standard USER Role Blocked",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "User unauthorized"
                                }
                            }
                        },
                        "Not Owner": {
                            "summary": "Investigator is not the Case Creator or the case doesn't exist",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Unauthorized to delete this evidence or record not found."
                                }
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "Not Found - Target case or evidence item does not exist.",
            "content": {
                "application/json": {
                    "examples": {
                        "Media Not Found": {
                            "summary": "Target evidence item does not exist as while as if the case does not exist",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Media not found."
                                }
                            }
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error - Storage or Database failure.",
            "content": {
                "application/json": {
                    "examples": {
                        "Database Error": {
                            "summary": "Database Failure",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": DATABASE_ERROR_MESSAGE
                                }
                            }
                        },
                        "Storage Error": {
                            "summary": "S3 / Object Storage Error",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Failed to delete stored object: ClientError"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
)
async def delete_evidence(
    case_id:str, 
    media_id:str,
    request: Request
):
    payload = verify_jwt(request)
    #Can raise the 401 errors
    

    user_role=payload.get("role")

    verify_not_user(user_role)
    #can raise HTTPException 403

    media_id = media_id_valid_uuid(media_id)
    # can raise HTTPException 400 
        
    try:

        case = Case(case_id=case_id)
        #raises 400 for bad case id format
        username=payload.get("username") if user_role == "INVESTIGATOR" else None
        response=await case.delete_evidence(media_id=media_id, jwt_username=username)
        #
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error", 
                "message": str(e)
            }
        )

def validate_comment_length(comment: str) -> bool:
        if not isinstance(comment, str):
            return False
        return len(comment.strip()) > 0

@router.post(
    "/cases/comments",
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Create comments",
    description="Creates a comment from the specific request body",
    status_code=201,
    responses={
        201: {
            "description": "Comment successfully created.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "comment": {
                            "commentId": 105,
                            "caseId": "123e4567-e89b-12d3-a456-426614174000",
                            "username": "InvestigatorJane",
                            "comment": "Reviewed the attached documents.",
                            "timestamp": "2026-08-12T11:01:30"
                        }
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Validation errors.",
            "content": {
                "application/json": {
                    "examples": {
                        "Invalid Comment": {
                            "summary": "Empty or invalid comment length",
                            "value": {
                                "status": "error", 
                                "message": "Comment must be a non-empty string"
                            }
                        }
                    }
                }
            }
        },
        401: INVALID_TOKEN_401,
        403: {
            "description": "Forbidden - Role-based access restrictions.",
            "content": {
                "application/json": {
                    "examples": {
                        "User Open Case Restriction": {
                            "summary": "USER role attempting to comment on an open case",
                            "value": {
                                "detail":{
                                    "status": "error",
                                    "message": "Users may only comment on closed cases"
                                }
                            }
                        },
                        "General Permission Denied": {
                            "summary": "Role lacks commenting privileges entirely",
                            "value": {
                                "detail":{
                                    "status": "error",
                                    "message":"Permission denied"
                                } 
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "Not Found - The requested case does not exist.",
            "content": {
                "application/json": {
                    "example": {
                        
                        "detail":{
                            "status": "error",
                            "message": CASE_NOT_FOUND
                        }
                    }
                }
            }
        },
        422: {
            "description": "Validation error - badly formatted request",
            "content": {
                "application/json": {
                    "examples": {
                        "Invalid CommenCaseID": {
                            "summary": "If the Case id is missing or not a uuid"
                        }
                    }
                }
            }
        },

    }
)
async def create_comment(
    body: create_comment_request,
    req: Request,
    connection: asyncpg.Connection = Depends(get_connection)
):
    payload = verify_jwt(req)
    # Need to document 

    role = payload.get("role")
    username = payload.get("username")

    if not body.comment or not validate_comment_length(body.comment):
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error", 
                "message": "Comment must be a non-empty string"
            }
        )

    case = Case(case_id=str(body.case_id))

    new_comment = await case.add_comment(
        connection,
        username,
        body.comment,
        role
    )

    return JSONResponse(
        status_code=201,
        content={
            "status": "success",
            "comment": new_comment
        }
    )
          
@router.delete(
    "/deleteCase",
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Deletes a case",
    description="Deletes a specific case and all attached elements within reason",
    responses={
        200: {
            "description": "Deletion of the case was successful.",
            "model": success_response,
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Case deleted successfully"
                    }
                }
            },
        },
        400:{
            "description": "Bad request - Missing Case id",
            "content":{
                "application/json":{
                    "examples":{
                        "Missing Payload ID": {
                            "summary": "Missing Case ID in Request Body",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Case id is missing"
                                }
                            }
                        },
                        "Poorly formated case id": {
                            "summary": "The case id is not a uuid",
                            "value": {
                                "detail":{
                                    "status": "error",
                                    "message": "fake-uuid is not a valid UUID format"
                                }
                            }
                        }
                    }
                }
            }
        },
        401: INVALID_TOKEN_401,
        403: {
            "description": "Forbidden - User lacks sufficient permissions",
            "content": {
                "application/json": {
                    "examples": {
                        "Role Forbidden": {
                            "summary": "Standard User Role Blocked",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "User unauthorized"
                                }
                            }
                        },
                        "Not Owner or Admin": {
                            "summary": "User is neither Case Creator nor Admin",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Only the case creator or an admin can delete this case"
                                }
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "Not Found - Resource does not exist",
            "content": {
                "application/json": {
                    "examples": {
                        "Case Not Found": {
                            "summary": "Target Case ID Not Found",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Case not found"
                                }
                            }
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error - Infrastructure failures",
            "content": {
                "application/json": {
                    "examples": {
                        "Database Error": {
                            "summary": "PostgreSQL Query Failure",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Database query failed"
                                }
                            }
                        },
                        "Storage Error": {
                            "summary": "S3 / MinIO Storage Failure",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Object storage Error"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
)
async def delete_case(case_request: CreateSingleCaseRequest, request: Request):

    payload = verify_jwt(request)
    
    verify_not_user(payload.get("role"))
    
    if not case_request.CaseID:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": CASE_ID_REQUIRED
            }
        )

    # Checkiing the uuid in constructor and keep object orientation.
    delete_case=Case(case_id=case_request.CaseID)

    try:
        await delete_case.delete_case(
            username=payload.get("username"),
            role=payload.get("role")
        )

        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Case deleted successfully"
            }
        )
    
    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
            }
        )

async def _save_annotations(
    connection: asyncpg.Connection,
    connector_id: UUID,
    annotations: str,
    user_name: str
):
    #This not in a class cases because it is faster to use the reportId in a query then to use the caseId and EvidenceId
    #report_id was changed to connector_id to prepare for the database change since the reports need to be de a one-to-many relationship and not one-to-one
    query = """
        UPDATE "Cases_DB"."Media" m
        SET MediaAnnotations = $1::jsonb
        FROM "Cases_DB"."Reports" r 
        INNER JOIN "Cases_DB"."Cases" c ON r.CaseId = c.CaseId
        WHERE m.MediaId = r.MediaId
          AND c.CaseCreator = $3 
          AND r.ReportId = $2;
    """
    try:
        await connection.execute(
            query, 
            annotations, 
            connector_id, 
            user_name
        )

    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
            }
        )

@router.post("/saveAnnotations", 
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Save Report Annotations",
    description="Updates the JSONB media annotations for a specific report/evidence item in PostgreSQL.",
    response_model=success_response,
    responses={
        200: {
            "description": "Annotations successfully saved.",
            "model": success_response,
            "content": {
                "application/json": {
                    "example": {
                        "status": "success"
                    }
                }
            },
        },
        401: {
            "description": "Unauthorized - JWT errors (missing, invalid, or expired)",
            "content": {
                "application/json": {
                    "examples": {
                        "Expired JWT": {
                            "summary": "JWT Token Expired",
                            "value": {
                                "status": "error",
                                "message": "Signature has expired."
                            }
                        },
                        "No authorization": {
                            "summary": "Missing JWT Cookie or Header",
                            "value": {
                                "status": "error",
                                "message": "Not authenticated"
                            }
                        },
                        "Invalid token": {
                            "summary": "Invalid JWT Signature/Malformed",
                            "value": {
                                "status": "error",
                                "message": "Invalid token"
                            }
                        },
                        "Invalid UUID": {
                            "summary": "Invalid Report UUID",
                            "value": {
                                "status": "error", 
                                "message": "badly formed hexadecimal UUID string"
                            }
                        }
                    }
                }
            },
        },
        403: {
            "description": "Forbidden - User does not have permission (e.g. Standard 'USER' role).",
            "model": error_response,
            "content": {
                "application/json": {
                    "example": {
                        "status": "error", 
                        "message": "User unauthorized"
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error - Database failure or unhandled exception.",
            "model": error_response,
            "content": {
                "application/json": {
                    "examples": {
                        "Database Error": {
                            "summary": "Database Failure",
                            "value": {
                                "detail": {
                                    "status": "error", 
                                    "message": "Database error"
                                }
                            }
                        },
                        "Server Exception": {
                            "summary": "Unexpected Error",
                            "value": {
                                "detail": {
                                    "status": "error", 
                                    "message": "An unexpected error occurred"
                                }
                            }
                        }
                    }
                }
            },
        },
    }
)
async def save_annotations(
    payload: save_snnotations_payload,
    request: Request,
    connection: asyncpg.Connection = Depends(get_connection)
):
    cookie=verify_jwt(request)
    user_role=cookie.get("role")
    # Checking authorization
    verify_not_user(user_role)
    user_name=cookie.get("username")

    try:
        connector_id=transform_to_uuid(payload.connector_id)
        annotations_json_str = json.dumps(payload.annotations)
        await _save_annotations(
            connection,
            connector_id,
            annotations_json_str,
            user_name
        )

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
            detail={
                "status": "error", 
                "message": str(e)
            }
        ) 

    
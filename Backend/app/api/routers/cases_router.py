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
    CASE_DELETE_NOT_ALLOWED,
    INTERNAL_SERVER_ERROR_STORAGE,
    DATABASE_ERROR_MESSAGE,
    set_audit_executor,
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
CASE_ID_REQUIRED = "CaseID required"
INVALID_CASE_ID = "Invalid CaseID"
CASE_NOT_FOUND_OR_UNAUTHORIZED = "Case not found or user unauthorized."
COOKIE_SCHEME=APIKeyCookie(name=COOKIE_NAME, auto_error=False)
USER_UNAUTHORIZED = "User unauthorized"
AUDIT_NOT_ALLOWED = "Only the case creator, the assigned investigator or an admin can view this audit log"
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

class audit_event(BaseModel):
    timestamp: str | None = Field(..., examples=["2026-05-20T19:43:02+00:00"])
    user: str | None = Field(..., examples=["investigator_user"])
    action: str | None = Field(..., examples=["UPDATE"])

class case_audit_response(BaseModel):
    status: str = Field(..., examples=["success"])
    caseID: str = Field(..., examples=["12345678-abcd-ef01-2345-6789abcdef01"])
    events: List[audit_event]

class audited_case(BaseModel):
    caseID: str = Field(..., examples=["12345678-abcd-ef01-2345-6789abcdef01"])
    caseName: str | None = Field(..., examples=["Reciepts sus"])
    eventCount: int | None = Field(..., examples=[5])
    lastEventTimestamp: str | None = Field(..., examples=["2026-05-20T19:43:02+00:00"])
    caseExists: bool | None = Field(..., examples=[True])

class audited_cases_response(BaseModel):
    status: str = Field(..., examples=["success"])
    cases: List[audited_case]

class create_case_request(BaseModel):
    title: str | None = None
    description: str | None = None

class create_single_case_request(BaseModel):
    CaseID: str | None = None

class assign_case_request(BaseModel):
    CaseID: str | None = None

class update_comment_request(BaseModel):
    comment: str

class update_case_request(BaseModel):
    CaseID: str | None = None
    CaseName: str | None = None
    CaseDescription: str | None = None

class create_comment_request(BaseModel):
    case_id: UUID
    comment: str | None = None

class save_annotations_payload(BaseModel):
    #Mapping from CamelCase to SnakeCase for Sonar to be Happy
    case_id: str = Field(..., alias="caseId")
    media_id: str = Field(..., alias="mediaId")
    #since the format of the annotations was not specified by frontend we will be accepting any valid JSON
    annotations: List[Dict[str, Any]]
    model_config = ConfigDict(populate_by_name=True)

class success_response(BaseModel):
    status: str = Field(..., examples=["success"])

class error_response(BaseModel):
    status: str = Field(..., examples=["error"])
    message: str = Field(..., examples=["Invalid token or database failure"])
  
def validate_case_assignment_request(request: Request, assign_request: assign_case_request):
    payload = verify_jwt(request)

    role = payload.get("role")
    user_id = payload.get("sub")
    username = payload.get("username")

    if role not in ["ADMIN", "INVESTIGATOR"]:
        raise HTTPException(
            status_code=403,
            detail={
                "status": "error",
                "message": "User unauthorized"
            }
        )

    if not assign_request.CaseID:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": CASE_ID_REQUIRED
            }
        )

    return user_id, username

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
    case.case_state = row["casestate"]
    case.case_assigned = row.get("caseassigned")
    case.case_creation_date = row["casecreationdate"]

    return case

def _format_case_evidence(row: dict, include_report: bool) -> dict:
    media_id = row["mediaid"]
    media_extension = row["mediaextension"] or ""
    media_bucket = row["mediabucket"]
    media_name = row["medianame"]
    target_filename = f"{media_id}{media_extension}"
    presign_client = get_object(for_presign=True)

    file_url = presign_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": media_bucket,
            "Key": target_filename
        },
        ExpiresIn=3600
    )

    evidence = {
        "mediaId": str(media_id),
        "casePerspective": row["caseperspective"],
        "mediaName": media_name,
        "mediaBucket": media_bucket,
        "mediaExtension": media_extension,
        "mediaTypeId": str(row["mediatypeid"]),
        "mediaUrl": file_url,
    }

    if include_report:
        evidence.update({
            "annotations": (
                json.loads(row["annotations"])
                if isinstance(row["annotations"], str)
                else (row["annotations"] or [])
            ),

            "reportArtifacts": (
                json.loads(row["reportartifacts"])
                if isinstance(row["reportartifacts"], str)
                else row["reportartifacts"]
            ),

            "reportFindings": row["reportfindings"],
            "reportComments": row["reportcomments"],
            "reportCertainty": row["reportcertainty"],
            
            "reportDateCreation": (
                row["reportdatecreation"].isoformat()
                if row["reportdatecreation"]
                else None
            ),
        })

    return evidence

def row_to_audit_event(row: dict) -> dict:
    return {
        "timestamp": row["eventtimestamp"].isoformat() if row["eventtimestamp"] else None,
        "user": row["eventuser"],
        "action": row["eventaction"]
    }

def _row_to_audited_case(row: dict) -> dict:
    return {
        "caseId": str(row["caseid"]),
        "caseName": row["casename"],
        "eventCount": row["eventcount"],
        "lastEventTimestamp": row["lasteventtimestamp"].isoformat() if row["lasteventtimestamp"] else None,
        "caseExists": row["caseexists"]
    }

@router.post(
    "/createCase",
    summary="Create a Case",
    status_code=201,
    dependencies=[Depends(COOKIE_SCHEME)],
    description="Creates a new case for an authenticated user. USER, INVESTIGATOR, and ADMIN roles may all create cases."
                " The case is always created in the OPEN state and is owned by the creator.",
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
async def create_case(
    case_request: create_case_request,
    request: Request,
    connection: Annotated[asyncpg.Connection, Depends(get_connection)]
):
    payload = verify_jwt(request)

    case = Case(
        case_name=case_request.title, 
        case_creator=payload.get("username"), 
        case_description=case_request.description
    )

    case_id = await case.create(connection,payload.get("sub"))

    return {
        "status": "success",
        "CaseId": case_id
    }

@router.get(
    "/getCases",
    dependencies=[Depends(COOKIE_SCHEME)],
    status_code=status.HTTP_200_OK,
    summary='List Cases',
    description=(
        "Returns all cases visible to the authenticated user. "
        "Any user can view cases they created, regardless of state. "
        "ADMIN and INVESTIGATOR users can additionally view all PUBLISHED "
        "and CLOSED cases. "
        "ADMIN and INVESTIGATOR users cannot view another user's OPEN case. "
        "USER accounts can only view cases they created."
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
                                "caseName": "Receipts sus",
                                "caseCreator": "normal_user",
                                "caseDescription": "Sus receipts case",
                                "caseState": "OPEN",
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

        403: USER_UNAUTHORIZED_403,

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
async def get_cases(request: Request, connection: Annotated[asyncpg.Connection, Depends(get_connection)]):
    payload = verify_jwt(request)
    role = payload.get("role")
    username = payload.get("username")

    try:
        if role == "USER":
            rows = await connection.fetch(
                """
                SELECT caseid, casecreator, casename, casedescription, casestate, casecreationdate
                FROM "Cases_DB"."Cases"
                WHERE casecreator = $1
                ORDER BY casecreationdate DESC
                """,
                username
            )

        elif role in ["ADMIN", "INVESTIGATOR"]:
            rows = await connection.fetch(
                """
                SELECT caseid, casecreator, casename, casedescription, casestate, casecreationdate
                FROM "Cases_DB"."Cases"
                WHERE 
                    casecreator = $1
                    OR casestate != 'OPEN'
                ORDER BY casecreationdate DESC
                """,
                username
            )

        else:
            raise HTTPException(
                status_code=403,
                detail={
                    "status": "error",
                    "message": "User unauthorized"
                }
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

@router.get(
    "/getSingleCase/{case_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Get a single case",
    description=(
        "Returns a single case with its comments and evidence. "
        "Any authenticated user can view a case they created, regardless of its state. "
        "ADMIN and INVESTIGATOR users can additionally view any PUBLISHED or CLOSED case. "
        "ADMIN and INVESTIGATOR users receive evidence annotations and report-related "
        "information whenever they can access the case. "
        "USER accounts only receive annotations and report-related information when "
        "the case is CLOSED."
    ),
    responses={
        200: {
            "description": "Case retrieved successfully.",
            "content": {
                "application/json": {
                    "examples": {
                        "Investigator or admin": {
                            "summary": (
                                "ADMIN or INVESTIGATOR viewing a PUBLISHED "
                                "or CLOSED case"
                            ),
                            "value": {
                                "status": "success",
                                "case": {
                                    "caseId": "12345678-abcd-ef01-2345-6789abcdef01",
                                    "caseName": "Flood in Westville",
                                    "caseCreator": "normal_user",
                                    "caseDescription": "Flood investigation case",
                                    "caseState": "PUBLISHED",
                                    "caseCreationDate": "2026-05-20T19:43:02+00:00"
                                },
                                "comments": [],
                                "evidence": [
                                    {
                                        "mediaId": "11111111-2222-3333-4444-555555555555",
                                        "casePerspective": "Front view",
                                        "mediaName": "flood_image.jpg",
                                        "mediaBucket": "images",
                                        "mediaExtension": ".jpg",
                                        "mediaTypeId": "99999999-8888-7777-6666-555555555555",
                                        "mediaUrl": "https://example.com/presigned-url",
                                        "annotations": [],
                                        "reportArtifacts": {},
                                        "reportFindings": "No manipulation detected.",
                                        "reportComments": "Reviewed by investigator.",
                                        "reportCertainty": 3,
                                        "reportDateCreation": "2026-05-21T10:15:00+00:00"
                                    }
                                ]
                            }
                        },

                        "User viewing own case": {
                            "summary": "USER viewing a case they created",
                            "value": {
                                "status": "success",
                                "case": {
                                    "caseId": "12345678-abcd-ef01-2345-6789abcdef01",
                                    "caseName": "Flood in Westville",
                                    "caseCreator": "normal_user",
                                    "caseDescription": "Flood investigation case",
                                    "caseState": "OPEN",
                                    "caseCreationDate": "2026-05-20T19:43:02+00:00"
                                },
                                "comments": [],
                                "evidence": [
                                    {
                                        "mediaId": "11111111-2222-3333-4444-555555555555",
                                        "casePerspective": "Front view",
                                        "mediaName": "flood_image.jpg",
                                        "mediaBucket": "images",
                                        "mediaExtension": ".jpg",
                                        "mediaTypeId": "99999999-8888-7777-6666-555555555555",
                                        "mediaUrl": "https://example.com/presigned-url"
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        },

        400: {
            "model": error_response,
            "description": "Bad Request - CaseId is malformed",
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

        403: USER_UNAUTHORIZED_403,

        404: {
            "model": error_response,
            "description": (
                "Not Found - Case does not exist or the authenticated user "
                "is not authorised to view it. USER accounts may only view "
                "cases they created. ADMIN and INVESTIGATOR accounts may view "
                "their own cases or any PUBLISHED or CLOSED case."
            ),
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
            "description": (
                "Internal Server Error - "
                + DATABASE_ERROR_MESSAGE
            ),
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
async def get_single_case(case_id: str, request: Request, connection: Annotated[asyncpg.Connection, Depends(get_connection)]):
    payload = verify_jwt(request)
    case_id = Case(case_id=case_id).case_id

    role = payload.get("role")
    username = payload.get("username")

    try:
        if role == "USER":
            row = await connection.fetchrow(
                """
                SELECT caseid, casecreator, casename, casedescription, casestate, casecreationdate, caseassigned
                FROM "Cases_DB"."Cases"
                WHERE caseid = $1 AND casecreator = $2
                """,
                case_id,
                username
            )

        elif role in ["ADMIN", "INVESTIGATOR"]:
            row = await connection.fetchrow(
                """
                SELECT caseid, casecreator, casename, casedescription, casestate, casecreationdate, caseassigned
                FROM "Cases_DB"."Cases"
                WHERE caseid = $1
                    AND (
                        casecreator = $2
                        OR casestate != 'OPEN'
                    )
                """,
                case_id,
                username
            )

        else:
            raise HTTPException(
                status_code=403,
                detail={
                    "status": "error",
                    "message": "User unauthorized"
                }
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
                ev.evidence_id AS "mediaid",
                ev.case_perspective AS "caseperspective",

                media.MediaAnnotations AS "annotations",
                media.ReportArtifacts AS "reportartifacts",
                media.ReportFindings AS "reportfindings",
                media.ReportComments AS "reportcomments",
                media.ReportCertainty AS "reportcertainty",
                media.ReportDateCreation AS "reportdatecreation",
                media.MediaUploadDate AS "mediauploaddate",

                m.MediaTypeId AS "mediatypeid",
                m.MediaName AS "medianame",
                m.MediaExtension AS "mediaextension",
                m.MediaBucket AS "mediabucket"

            FROM "Cases_DB"."Cases" c

            CROSS JOIN LATERAL
                unnest(c.evidence)
                AS ev(evidence_id, case_perspective)

            JOIN "Cases_DB"."Media" media
                ON media.MediaId = ev.evidence_id

            JOIN "Cases_DB"."MediaType" m
                ON media.MediaType = m.MediaTypeId

            WHERE c.CaseId = $1
            """,
            case_id,
        )

        can_view_report = role in ["ADMIN", "INVESTIGATOR"] or row["casestate"] == "CLOSED"

        return jsonable_encoder({
            "status": "success",
            "case": case.to_json(),
            "comments": await case.get_comments(connection),
            "evidence": [
                _format_case_evidence(evidence_row, include_report=can_view_report)
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
        "Uploads a media file as evidence against an open case. Only the user "
        "who owns the case may upload to it, regardless of role. The file is "
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
    connection: Annotated[asyncpg.Connection, Depends(get_connection)]
):
    payload = verify_jwt(request)

    #verify_not_user(payload.get("role"))
    #Now open to all roles

    case_creator = payload["username"]
    executor_id=payload.get("sub")

    # Case.__init__ validates the UUID and raises a 400 on a malformed value
    validated_case_id = Case(case_id=case_id).case_id

    try:
        await set_audit_executor(connection, executor_id)
        row = await connection.fetchrow(
            """
            SELECT caseid, casecreator, casename, casedescription, casestate, casecreationdate
            FROM "Cases_DB"."Cases"
            WHERE caseid = $1
                AND casecreator = $2
                AND casestate = 'OPEN'
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

        result = await case.add_evidence(
            media, 
            validated_case_id, 
            connection, 
            executor_id
        )

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

@router.patch(
    "/closeCase",
    status_code=200,
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Close an assigned published case",
    description=(
        "Closes a PUBLISHED case assigned to the currently authenticated "
        "ADMIN or INVESTIGATOR. The case must be assigned to the user making "
        "the request and must not have been created by that same user."
    ),
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
            "description": "Bad Request - Case ID missing",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": CASE_ID_REQUIRED
                        }
                    }
                }
            }
        },

        403: USER_UNAUTHORIZED_403,

        404: {
            "description": "Case not found or user unauthorized to close it",
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
async def close_case(
    case_request: create_single_case_request,
    request: Request,
    connection: Annotated[asyncpg.Connection, Depends(get_connection)]
):
    payload = verify_jwt(request)
    role = payload.get("role")

    if role not in ["INVESTIGATOR", "ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail={
                "status": "error",
                "message": "User unauthorized"
            }
        )

    user_id = payload.get("sub")
    username = payload.get("username")
    
    if not case_request.CaseID:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": CASE_ID_REQUIRED
            }
        )
    
    try:
        async with connection.transaction():
            await set_audit_executor(connection, user_id)
            row = await connection.fetchrow(
                """
                UPDATE "Cases_DB"."Cases"
                SET casestate = 'CLOSED', caseclosedate = CURRENT_TIMESTAMP
                WHERE caseid = $1::uuid
                    AND casestate = 'PUBLISHED'
                    AND caseassigned = $2
                RETURNING *;
                """ ,
                case_request.CaseID,
                username
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
        "Updates the name and/or the description of a case. USER, INVESTIGATOR and "
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
    case_request: update_case_request,
    request: Request,
    connection: Annotated[asyncpg.Connection, Depends(get_connection)]
):
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
        validated_name = Case(case_name=case_request.CaseName).case_name

    try:
        await set_audit_executor(connection, payload.get("sub"))
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
    update_data: update_comment_request,
    request: Request,
    connection: Annotated[asyncpg.Connection, Depends(get_connection)]
):
    payload = verify_jwt(request)

    case_uuid = Case(case_id=case_id).case_id
    executor_id=payload.get("sub")
    
    try:
        async with connection.transaction():
            await set_audit_executor(connection, executor_id)
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
    connection: Annotated[asyncpg.Connection, Depends(get_connection)]
):
    payload = verify_jwt(request)
    username = payload.get("username")
    executor_id=payload.get("sub")
    
    try:
        async with connection.transaction():
            await set_audit_executor(connection, executor_id)
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
    request: Request,
    connection: Annotated[asyncpg.Connection, Depends(get_connection)]
):

    payload = verify_jwt(request)
    user_role=payload.get("role")
    verify_not_user(user_role) 

    try:
        case = Case(case_id=case_id)
        comments_data= await case.get_comments(connection)

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
    description=(
        "Deletes a specific evidence item/media attached to a case. Only the case "
        "owner may delete evidence from an OPEN case. ADMIN users may delete "
        "evidence from any case state."
    ),
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
            "description": "Forbidden - The caller does not own the case or the case is not OPEN.",
            "content": {
                "application/json": {
                    "examples": {
                        "Not Case Owner": {
                            "summary": "Caller does not own the case",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "User unauthorized"
                                }
                            }
                        },
                        "Case Not Open": {
                            "summary": "Case is not open",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "User unauthorized"
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
    request: Request,
    connection: Annotated[asyncpg.Connection, Depends(get_connection)]
):
    payload = verify_jwt(request)
    #Can raise the 401 errors
    
    #verify_not_user(user_role)
    #There is no limmit to who can delete now

    media_id = media_id_valid_uuid(media_id)
    # can raise HTTPException 400 
        
    try:

        case = Case(case_id=case_id)
        #raises 400 for bad case id format
        username=payload.get("username")
        response=await case.delete_evidence(
            media_id=media_id,
            connection=connection,
            jwt_username=username,
            jwt_user_id=payload.get("sub"),
            is_admin=payload.get("role") == "ADMIN"
        )
        #
        
        return response
    except HTTPException:
        raise
    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
            }
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
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
    connection: Annotated[asyncpg.Connection, Depends(get_connection)]
):
    payload = verify_jwt(req)
    # Need to document 

    role = payload.get("role")
    username = payload.get("username")
    executor_id= payload.get("sub")

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
        role,
        executor_id
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
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Deletes a case",
    description=(
        "Deletes a case together with any evidence only it referenced. USER, "
        "INVESTIGATOR and ADMIN may all delete a case they created, but only while it "
        "is still OPEN. An Admin may delete any case in any state."
    ),
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
                                    "message": "CaseID required"
                                }
                            }
                        },
                        "Poorly formated case id": {
                            "summary": "The case id is not a uuid",
                            "value": {
                                "detail":{
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
            "description": "Forbidden - not the creator, or the case is no longer open",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": CASE_DELETE_NOT_ALLOWED
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
                                    "message": DATABASE_ERROR_MESSAGE
                                }
                            }
                        },
                        "Storage Error": {
                            "summary": "S3 / MinIO Storage Failure",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Failed to delete stored object 1234.png: connection refused"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
)
async def delete_case(
    case_request: create_single_case_request,
    request: Request,
    connection: Annotated[asyncpg.Connection, Depends(get_connection)]
):

    payload = verify_jwt(request)
    
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
            is_admin=payload.get("role") == "ADMIN",
            connection=connection,
            executor_id=payload.get("sub")
        )

        return {
            "status": "success",
            "message": "Case deleted successfully"
        }
    
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
    case_id: UUID,
    media_id: UUID,
    annotations: str,
    user_name: str,
    executor_id: str | None = None
):
        # Evidence is stored as a composite array on the case rather than in a join table.
    query = """
        UPDATE "Cases_DB"."Media" m
        SET MediaAnnotations = $1::jsonb
        FROM "Cases_DB"."Cases" c
        CROSS JOIN LATERAL unnest(c.evidence) AS evidence(evidence_id, case_perspective)
        WHERE m.MediaId = evidence.evidence_id
            AND c.CaseId = $2
            AND m.MediaId = $3
            AND c.CaseAssigned = $4
            AND c.CaseState = 'PUBLISHED'
        RETURNING m.MediaId;
    """
    try:
        async with connection.transaction():
            if executor_id:
                await set_audit_executor(connection, executor_id)

            updated_row = await connection.fetchrow(
                query, 
                annotations, 
                case_id,
                media_id,
                user_name
            )

            if updated_row is None:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "status": "error",
                        "message": USER_UNAUTHORIZED
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
    payload: save_annotations_payload,
    request: Request,
    connection: Annotated[asyncpg.Connection, Depends(get_connection)]
):
    cookie=verify_jwt(request)
    user_role=cookie.get("role")
    # Checking authorization
    verify_not_user(user_role)
    user_name=cookie.get("username")
    executor_id=cookie.get("sub")

    try:
        case_id=transform_to_uuid(payload.case_id)
        media_id=transform_to_uuid(payload.media_id)
        annotations_json_str = json.dumps(payload.annotations)
        await _save_annotations(
            connection,
            case_id,
            media_id,
            annotations_json_str,
            user_name,
            executor_id
        )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success"
            }
        )

    except HTTPException:
        raise
    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
            }
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
            }
        )

@router.get(
    "/getAudit/caseID/{case_id}",
    status_code=status.HTTP_200_OK,
    tags=["Audit"],
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Get all aduit logs for a case",
    description=(
        "Returns every audited event recorded against a case. "
        "Covers case creation, renaming, description edits, publishing, assignment, "
        "closing and deletion, as along with evidence added to or annotated on the case. "
        "The case creator may read their own case, an INVESTIGATOR may read a case "
        "assigned to them, and an ADMIN may read any case. The timeline stays readable "
        "after a case is deleted. A case with no audit logs will return an empty list."
    ),
    responses={
        200: {
            "model": case_audit_response,
            "description": "Audit trail retrieved successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "caseID": "123e4567-e89b-12d3-a456-426614174000",
                        "events": [
                            {
                                "timestamp": "2026-08-12T11:01:30",
                                "user": "invetigator_user",
                                "action": "Case Closed"
                            }
                        ]
                    }
                }
            }   
        },

        400: {
            "model": error_response,
            "description": "Bad Request - CaseID is not a valid UUID",
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

        403: {
            "description": "Forbidden - not the creator, the assigned investigator or an admin",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "status": "error",
                            "message": AUDIT_NOT_ALLOWED
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
async def get_case_audit_events(
    case_id: str,
    request: Request,
    connection: Annotated[asyncpg.Connection, Depends(get_connection)]
):
    payload = verify_jwt(request)

    validated_case_id = Case(case_id=case_id).case_id

    username = payload.get("username")
    is_admin = payload.get("role") == "ADMIN"

    try:
        if not is_admin:
            ownership = await connection.fetchrow(
                """
                SELECT
                    COALESCE(cases.casecreator, audit.old_casecreator) AS casecreator,
                    COALESCE(cases.caseassigned, audit.old_caseassigned) AS caseassigned
                FROM (SELECT $1::uuid AS caseid) AS target
                LEFT JOIN "Cases_DB"."Cases" AS cases
                    ON cases.caseid = target.caseid
                LEFT JOIN LATERAL (
                    SELECT old_casecreator, old_caseassigned
                    FROM "Cases_DB"."Audit_Cases"
                    WHERE old_case_id = target.caseid
                    ORDER BY audit_case_id DESC
                    LIMIT 1
                ) AS audit ON TRUE
                """,
                validated_case_id
            )

            if username not in (ownership["casecreator"], ownership["caseassigned"]):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "status": "error",
                        "message": AUDIT_NOT_ALLOWED
                    }
                )

        rows = await connection.fetch(
            """
            WITH case_audit AS (
                SELECT
                    audit_case_id AS ordinal,
                    audittimestamp,
                    query_executor_name,
                    query_type::text AS query_type,
                    old_casename,
                    old_casedescription,
                    old_casestate,
                    old_caseassigned
                FROM "Cases_DB"."Audit_Cases"
                WHERE old_case_id = $1::uuid


            UNION ALL

            SELECT
                214783647,
                NULL::timestamptz,
                NULL::varchar,
                NULL::text,
                cases.casename,
                cases.casedescription,
                cases.casestate,
                cases.caseassigned
            FROM "Cases_DB"."Cases" AS cases
            WHERE cases.caseid = $1::uuid
            ),
            case_transitions AS (
                SELECT
                    audittimestamp,
                    query_executor_name,
                    query_type,
                    old_casename,
                    old_casedescription,
                    old_casestate,
                    old_caseassigned,
                    LEAD(old_casename) OVER (ORDER BY ordinal) AS next_casename,
                    LEAD(old_casedescription) OVER (ORDER BY ordinal) AS next_casedescription,
                    LEAD(old_casestate) OVER (ORDER BY ordinal) AS next_casestate,
                    LEAD(old_caseassigned) OVER (ORDER BY ordinal) AS next_caseassigned
                FROM case_audit
            ),
            audit_events AS (
                SELECT
                    audittimestamp AS eventtimestamp,
                    query_executor_name AS eventuser,
                    CASE
                        WHEN query_type = 'INSERT' THEN 'Case Created'
                        WHEN query_type = 'DELETE' THEN 'Case Deleted'
                        WHEN next_casestate IS DISTINCT FROM old_casestate
                            AND next_casestate = 'PUBLISHED' THEN 'Case Published'
                        WHEN next_casestate IS DISTINCT FROM old_casestate
                            AND next_casestate = 'CLOSED' THEN 'Case Closed'
                        WHEN next_casestate IS DISTINCT FROM old_casestate
                            AND next_casestate = 'OPEN' THEN 'Case Reopened'
                        WHEN old_caseassigned IS NULL
                            AND next_caseassigned IS NOT NULL THEN 'Case Assigned'
                        WHEN old_caseassigned IS NOT NULL
                            AND next_caseassigned IS NULL THEN 'Case Unassigned'
                        WHEN old_casename IS DISTINCT FROM next_casename
                            AND old_casedescription IS DISTINCT FROM next_casedescription
                            THEN 'Case Renamed and Description Updated'
                        WHEN old_casename IS DISTINCT FROM next_casename
                            THEN 'Case Renamed'
                        WHEN old_casedescription IS DISTINCT FROM next_casedescription
                            THEN 'Case Description Updated'
                        ELSE 'Case Updated'
                    END AS eventaction
                FROM case_transitions
                WHERE query_type IS NOT NULL

                UNION ALL

                SELECT
                    audit_media.audittimestamp AS eventtimestamp,
                    audit_media.query_executor_name AS eventuser,
                    CASE audit_media.query_type::text
                        WHEN 'INSERT' THEN 'Evidence Added'
                        ELSE 'Evidence Annotated'
                    END AS eventaction
                    FROM "Cases_DB"."Audit_Media" AS audit_media
                    INNER JOIN "Cases_DB"."Cases" AS cases
                        ON cases.caseid = $1::uuid
                    CROSS JOIN LATERAL unnest(
                        COALESCE(cases.evidence, ARRAY[]::"Cases_DB".evidence_type[])
                    ) AS elem
                    WHERE elem.evidence_id = audit_media.old_media_id
                        AND audit_media.query_type::text IN ('INSERT', 'UPDATE')
            )
            SELECT
                audit_events.eventtimestamp AS eventtimestamp,
                audit_events.eventuser AS eventuser,
                audit_events.eventaction AS eventaction
            FROM audit_events
            ORDER BY audit_events.eventtimestamp DESC NULLS LAST
            """,
            validated_case_id
        )

        return {
            "status": "success",
            "caseID": validated_case_id,
            "events": [row_to_audit_event(row) for row in rows]
        }

    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
            }
        )

@router.get(
    "/getAllAudit",
    status_code=status.HTTP_200_OK,
    tags=["Audit"],
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Get all cases with audit logs",
    description=(
        "Returns the different cases that have at least one audit entry, with the number of recorded events"
        " and when the most recent one happened. Amdin only."
    ),
    responses={
        200: {
            "model": audited_cases_response,
            "description": "Audited cases retrieved successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "cases": [
                            {
                                "caseId": "123e4567-e89b-12d3-a456-426614174000",
                                "caseName": "Reciepts sus",
                                "eventCount": 5,
                                "lastEventTimnestamp": "2026-08-12T11:01:30",
                                "caseExists": True
                            },
                            {
                                "caseId": "987e6543-e21b-12d3-a456-426614174000",
                                "caseName": "Idk ig",
                                "eventCount": 2,
                                "lastEventTimnestamp": None,
                                "caseExists": False
                            }
                        ]
                    }
                }
            }
        },

        401: INVALID_TOKEN_401,

        403: USER_UNAUTHORIZED_403,

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
async def get_audited_cases(
    request: Request,
    connection: Annotated[asyncpg.Connection, Depends(get_connection)]
):
    payload = verify_jwt(request)

    if payload.get("role") != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail={
                "status": "error",
                "message": USER_UNAUTHORIZED
            }
        )
    
    try:
        rows = await connection.fetch(
            """
            WITH audit_events AS (
                SELECT old_case_id AS caseid,
                    audittimestamp AS eventtimestamp,
                    query_executor_name AS eventuser,
                    query_type::text AS eventaction
                FROM "Cases_DB"."Audit_Cases"
                WHERE old_case_id IS NOT NULL

                UNION ALL

                SELECT old_caseid AS caseid,
                    audittimestamp AS eventtimestamp,
                    query_executor_name AS eventuser,
                    query_type::text AS eventaction
                FROM "Cases_DB"."Audit_Comments"
                WHERE old_caseid IS NOT NULL
            ),
            audit_summary AS (
                SELECT
                    audit_events.caseid AS caseid,
                    COUNT(*) AS eventcount,
                    MAX(audit_events.eventtimestamp) AS lasteventtimestamp
                FROM audit_events
                GROUP BY audit_events.caseid
            )
            SELECT
                audit_summary.caseid AS caseid,
                COALESCE(cases.casename,
                    (SELECT audit_cases.old_casename
                    FROM "Cases_DB"."Audit_Cases" AS audit_cases
                    WHERE audit_cases.old_case_id = audit_summary.caseid
                    ORDER BY audit_cases.audittimestamp DESC NULLS LAST
                    LIMIT 1
                )
            ) AS casename,
            audit_summary.eventcount AS eventcount,
            audit_summary.lasteventtimestamp AS lasteventtimestamp,
            (cases.caseid IS NOT NULL) AS caseexists
            FROM audit_summary
            LEFT JOIN "Cases_DB"."Cases" AS cases
                ON cases.caseid = audit_summary.caseid
            ORDER BY audit_summary.lasteventtimestamp DESC NULLS LAST
            """
        )

        return {
            "status": "success",
            "cases": [_row_to_audited_case(row) for row in rows]
        }

    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
            }
        )

@router.patch(
    "/assignCase",
    status_code=200,
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Assign the current investigator or admin to a case",
    description=(
        "Assigns the currently authenticated ADMIN or INVESTIGATOR to a case. "
        "The case must be published, unassigned, and must not have been created "
        "by the user making the request."
    ),
    responses={
        200: {
            "description": "Case assigned successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Case assigned successfully"
                    }
                }
            }
        },

        400: {
            "description": "Bad Request - Invalid assignment request",
            "content": {
                "application/json": {
                    "examples": {
                        "missing_case_id": {
                            "summary": "Case ID missing",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": CASE_ID_REQUIRED
                                }
                            }
                        },
                        "invalid_assignment": {
                            "summary": "Case cannot be assigned",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Invalid assignment request"
                                }
                            }
                        }
                    }
                }
            }
        },

        403: USER_UNAUTHORIZED_403,

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
async def assign_case(
    assign_request: assign_case_request, 
    request: Request, 
    connection: Annotated[asyncpg.Connection, Depends(get_connection)]
):
    user_id, username = validate_case_assignment_request(
        request,
        assign_request
    )

    try:
        async with connection.transaction():
            await set_audit_executor(connection, user_id)
            row = await connection.fetchrow(
                """
                UPDATE "Cases_DB"."Cases"
                SET caseassigned = $1
                WHERE caseid = $2::uuid
                    AND caseassigned IS NULL
                    AND casestate = 'PUBLISHED'
                    AND casecreator != $1
                RETURNING *;
                """,
                username,
                assign_request.CaseID
            )

            if row is None:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "status": "error",
                        "message": "Invalid assignment request"
                    }
                )

        return {
            "status": "success",
            "message": "Case assigned successfully"
        }

    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
            }
        )

@router.patch(
    "/unassignCase",
    status_code=200,
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Unassign the current investigator or admin from a case",
    description=(
        "Unassigns the currently authenticated ADMIN or INVESTIGATOR from a case. "
        "The case must be published, must currently be assigned to the user making "
        "the request, and must not have been created by that user."
    ),
    responses={
        200: {
            "description": "Case unassigned successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Case unassigned successfully"
                    }
                }
            }
        },

        400: {
            "description": "Bad Request - Invalid unassignment request",
            "content": {
                "application/json": {
                    "examples": {
                        "missing_case_id": {
                            "summary": "Case ID missing",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": CASE_ID_REQUIRED
                                }
                            }
                        },
                        "invalid_unassignment": {
                            "summary": "Case cannot be unassigned",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Invalid unassignment request"
                                }
                            }
                        }
                    }
                }
            }
        },

        403: USER_UNAUTHORIZED_403,

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
async def unassign_case(
    assign_request: assign_case_request, 
    request: Request, 
    connection: Annotated[asyncpg.Connection, Depends(get_connection)]
):
    user_id, username = validate_case_assignment_request(
        request,
        assign_request
    )

    try:
        async with connection.transaction():
            await set_audit_executor(connection, user_id)

            row = await connection.fetchrow(
                """
                UPDATE "Cases_DB"."Cases"
                SET caseassigned = NULL
                WHERE caseid = $2::uuid
                    AND caseassigned = $1
                    AND casestate = 'PUBLISHED'
                    AND casecreator != $1
                RETURNING *;
                """,
                username,
                assign_request.CaseID
            )

            if row is None:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "status": "error",
                        "message": "Invalid unassignment request"
                    }
                )

        return {
            "status": "success",
            "message": "Case unassigned successfully"
        }

    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
            }
        )

@router.patch(
    "/publishCase",
    status_code=200,
    dependencies=[Depends(COOKIE_SCHEME)],
    summary="Publish an open case",
    description=(
        "Publishes an OPEN case owned by the currently authenticated user. "
        "The case must exist, must currently be in the OPEN state, and the "
        "authenticated user must be the case creator."
    ),
    responses={
        200: {
            "description": "Case published successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Case published successfully"
                    }
                }
            }
        },


        400: {
            "description": "Bad Request - Invalid publish request",
            "content": {
                "application/json": {
                    "examples": {
                        "missing_case_id": {
                            "summary": "Case ID missing",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": CASE_ID_REQUIRED
                                }
                            }
                        },
                        "invalid_publish": {
                            "summary": "Case cannot be published",
                            "value": {
                                "detail": {
                                    "status": "error",
                                    "message": "Invalid publish request"
                                }
                            }
                        }
                    }
                }
            }
        },

        403: USER_UNAUTHORIZED_403,

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
async def publish_case(
    publish_request: assign_case_request,
    request: Request, 
    connection: Annotated[asyncpg.Connection, Depends(get_connection)]
):
    payload = verify_jwt(request)
    user_id = payload.get("sub")
    username = payload.get("username")
    role = payload.get("role")

    if role not in ["INVESTIGATOR", "ADMIN", "USER"]:
        raise HTTPException(
            status_code=403,
            detail={
                "status": "error",
                "message": "User unauthorized"
            }
        )


    if not publish_request.CaseID:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": CASE_ID_REQUIRED
            }
        )

    try:
        async with connection.transaction():
            await set_audit_executor(connection, user_id)

            row = await connection.fetchrow(
                """
                UPDATE "Cases_DB"."Cases"
                SET casestate = 'PUBLISHED', casepublishdate = CURRENT_TIMESTAMP
                WHERE caseid = $1::uuid
                    AND casestate = 'OPEN'
                    AND casecreator = $2
                RETURNING *;
                """,
                publish_request.CaseID,
                username
            )

            if row is None:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "status": "error",
                        "message": "Invalid publish request"
                    }
                )

        return {
            "status": "success",
            "message": "Case published successfully"
        }
                
    except asyncpg.PostgresError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": DATABASE_ERROR_MESSAGE
            }
        )

import uuid
from uuid import uuid4
import asyncpg
import asyncio
import io
import hashlib
from botocore.exceptions import BotoCoreError, ClientError, EndpointConnectionError
from fastapi import UploadFile, HTTPException
from pathlib import Path
from pypdf import PdfReader
from datetime import datetime, timedelta, timezone
import boto3
from botocore.client import Config
from app.core.env import Other_Settings, Minio_Settings, R2_Settings
from mypy_boto3_s3 import S3Client
from app.core.media_relay import MediaRelay

CASE_NOT_FOUND = "Case not found"
MISSING_CASE_ID = "Case id is missing"
CASE_ALREADY_EXISTS = "This case already exists"
PDF_SCRIPTS_NOT_ALLOWED = "We don't allow scripts in pdfs. They are a security concern."
PDF_VERIFICATION_FAILED = "Could not verify PDF security. File rejected."
INVALID_PDF_PREFIX = "Invalid or corrupted PDF file: "
INVALID_CASE_ID_UUID = "Invalid case_id UUID"
UNSUPPORTED_EXTENSION_PREFIX = "Unsupported file extension: "
MEDIA_ALREADY_ON_CASE = "Image already associated with this case"
INTERNAL_SERVER_ERROR = "Internal server error"
INTERNAL_SERVER_ERROR_STORAGE = "Evidence storage is temporarily unavailable. Please try again."
DATABASE_ERROR_MESSAGE = "Database error"
CASE_DELETE_NOT_ALLOWED = "Only the creator of an open case or an admin can delete this case"
STORAGE_DELETE_FAILED_PREFIX = "Failed to delete stored object "

FILE_TOO_LARGE = "File exceeds the maximum allowed size of 50MB"
 
MAX_UPLOAD_SIZE_BYTES = 50 * 1048576  # 50MB this is later going to be a env
# 1MB = 1024 times 1024

minio_settings = Minio_Settings()
other_settings = Other_Settings()
r2_settings= R2_Settings()


async def set_audit_executor(connection: asyncpg.Connection, executor_id: str | uuid.UUID | None):
    if executor_id is None:
        return

    await connection.execute(
        "SELECT set_config('app.current_user_id', $1, false)",
        str(executor_id),
    )


def get_object(for_presign: bool = False) -> S3Client:
    if other_settings.ENVIRONMENT == "development":

        if for_presign:
            minio_domain = minio_settings.MINIO_EXTERNAL_URL
        else:
            minio_domain = minio_settings.STORAGE_URL
        
        
        if not minio_domain.startswith(("http://", "https://")):
            minio_domain = f"http://{minio_domain}"

        return boto3.client(
            "s3",
            endpoint_url=minio_domain,
            aws_access_key_id=minio_settings.MINIO_ROOT_USER,
            aws_secret_access_key=minio_settings.MINIO_ROOT_PASSWORD,
            region_name=minio_settings.AWS_REGION,
            config=Config(
                signature_version="s3v4",
                s3={
                    "addressing_style": "path"
                }
            ),
        )

    elif other_settings.ENVIRONMENT == "production":
        cloud_url = r2_settings.R2_URL
        
        if not cloud_url.startswith(("http://", "https://")):
            cloud_url = f"https://{cloud_url}"

        key_id=r2_settings.R2_ACCESS_KEY_ID
        secret=r2_settings.R2_SECRET_ACCESS_KEY

        return boto3.client(
            "s3",
            endpoint_url=cloud_url,
            aws_access_key_id=key_id,
            aws_secret_access_key=secret,
            region_name="auto",
            config=Config(
                signature_version="s3v4",
                s3={
                    "addressing_style": "path"
                }
            ),
        )


#helper to lessen the complexity of the constructor for the case class.
def check_case_creator_valid(case_creator):
    if not case_creator.strip():
        raise HTTPException(
            status_code=400,
                detail={
                    "status": "error",
                    "message": "CaseCreator is required"
                }
            )

    if  len(case_creator) > 100:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message":"Name is too long. Must be 100 characters or less"
            }
        )

# The helper function that checks the file chunk by chunk
async def read_upload_with_size_limit(media: UploadFile) -> bytes:
    chunks = []
    total = 0
 
    while True:
        chunk = await media.read(1048576)
        if not chunk:
            break
 
        total += len(chunk)
        if total > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail={
                    "status": "error",
                    "message": FILE_TOO_LARGE
                }
            )
 
        chunks.append(chunk)
 
    return b"".join(chunks)
 

# pdf script detection helper
def pdf_script_helper(file_bytes):
    try:
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)

        try: 
            root = reader.trailer.get("/Root", {}) #checking for automatic triggers
            if root:
                root = root.get_object()
                if "/OpenAction" in root or "/AA" in root:
                    raise HTTPException(
                        status_code=400, 
                        detail={
                            "status": "error",
                            "message": PDF_SCRIPTS_NOT_ALLOWED
                        }
                    )

                if "/Names" in root:
                    names=root["/Names"].get_object()
                    if "/JavaScript" in names:
                        raise HTTPException(
                            status_code=400,
                            detail={
                                "status": "error",
                                "message": PDF_SCRIPTS_NOT_ALLOWED
                            }
                        )
        except HTTPException:
            raise
        except KeyError :
            pass
        except Exception :
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": PDF_VERIFICATION_FAILED
                }
            ) 
    except HTTPException:
        raise 
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail={
                "status": "error",
                "message": f"{INVALID_PDF_PREFIX}{str(e)}"
            }
        )
                   

async def collect_orphan_media(connection: asyncpg.Connection, evidence) -> list[dict]:
    """
    Deletes the Media rows for evidence no longer referenced by any case and returns
    what was removed, so the stored objects can be cleaned up afterwards.
    """
    orphan_media = []

    # Each element is the composite evidence_type(evidence_id, case_perspective),
    # which asyncpg returns as a tuple, so the id is read positionally.
    for evidence_item in evidence:
        media_id = evidence_item[0]

        remaining_media_references = await connection.fetchval(
            """
            SELECT COUNT(*)
            FROM "Cases_DB"."Cases" other_case,
                 unnest(COALESCE(other_case.evidence, ARRAY[]::"Cases_DB".evidence_type[])) AS elem
            WHERE elem.evidence_id = $1
            """,
            media_id
        )

        # Still attached to another case, so it is not an orphan.
        if remaining_media_references:
            continue

        deleted_media = await connection.fetchrow(
            """
            DELETE FROM "Cases_DB"."Media" media
            USING "Cases_DB"."MediaType" media_type
            WHERE media.MediaId = $1
                AND media.MediaType = media_type.MediaTypeId
            RETURNING
                media.MediaId AS mediaid,
                media_type.MediaBucket AS mediabucket,
                media_type.MediaExtension AS mediaextension
            """,
            media_id
        )

        if deleted_media is not None:
            orphan_media.append({
                "mediaid": deleted_media["mediaid"],
                "mediabucket": deleted_media["mediabucket"],
                "mediaextension": deleted_media["mediaextension"]
            })

    return orphan_media


async def delete_stored_objects(orphan_media: list[dict]):
    """
    Removes the orphaned objects from object storage. Runs after the database
    transaction has committed.
    """
    storage_client = get_object()

    for media in orphan_media:
        object_name = f"{media['mediaid']}{media['mediaextension']}"

        try:
            await asyncio.to_thread(
                storage_client.delete_object,
                Bucket=media["mediabucket"],
                Key=object_name
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": f"{STORAGE_DELETE_FAILED_PREFIX}{object_name}: {e}"
                }
            )


# If the case_id is None then the case is not in the db. You may call create().
# When the case_id is not None then we know the case exists in the db. Time and Id is adjusted after create() is called.
class Case:
    def __init__(
        self, 
        case_creator: str = None, 
        case_name: str = None, 
        case_description: str=None, 
        case_id: str=None
    ):
        if  (case_creator is not None):
            check_case_creator_valid(case_creator)
        if  (case_name is not None):
            if not case_name.strip():
                raise HTTPException(
                    status_code=400,
                    detail={
                        "status": "error",
                        "message":"CaseName is required"
                    }
                )
            if len(case_name) > 255:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "status": "error",
                        "message":"CaseName must be 255 characters or less"
                    }
                )
        
        self.case_creator = None if case_creator is None else case_creator.strip()
        self.case_name = None if case_name is None else case_name.strip()
        self.case_description = case_description
        self.case_state = "OPEN"
        self.case_assigned = None
        if case_id is not None:
            cleaned_id = case_id.strip()
            try:
                uuid.UUID(cleaned_id)
                self.case_id  = cleaned_id
            except ValueError:
                raise HTTPException(
                    status_code= 400,
                    detail={
                        "status": "error",
                        "message": f"'{case_id}' is not a valid UUID format"
                    } 
                )
        else:
            self.case_id = None
        self.case_creation_date = None

    async def create(self, connection: asyncpg.Connection, user_id):
        if self.case_id  is not None:
            raise HTTPException(
                status_code=409,
                detail={
                    "status": "error",
                    "message": CASE_ALREADY_EXISTS
                }
            )
        await set_audit_executor(connection, user_id)
        try:
            row = await connection.fetchrow(
                """
                INSERT INTO "Cases_DB"."Cases"
                (casecreator, casename, casedescription, casestate)
                VALUES ($1, $2, $3, $4::case_state_enum)
                RETURNING caseid, casecreationdate
                """,
                self.case_creator,
                self.case_name,
                self.case_description,
                self.case_state
            )
        except asyncpg.PostgresError:
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": DATABASE_ERROR_MESSAGE
                }
            )

        self.case_id=row["caseid"]
        self.case_creation_date=row["casecreationdate"]
        return str(row["caseid"])

    async def add_evidence(
        self,
        media: UploadFile,
        case_id: uuid.UUID,
        connection: asyncpg.Connection,
        executor_id
    ):
        filename = media.filename
        local_extension = Path(filename).suffix.lower() #extract of the extension (e.g: .png)
        #Cannot trust the supplied extension ever
        file_bytes = await read_upload_with_size_limit(media) # Cannot trust supplied file size.
        await media.seek(0)
        #script detection
        if local_extension == ".pdf":
            pdf_script_helper(file_bytes)
            
        # It is impossible for case id to be an invalid uuid since it is typed to UUID

        try:
            async with connection.transaction():
                await set_audit_executor(connection, executor_id)

                type_record = await connection.fetchrow(
                    """
                    SELECT 
                        MediaTypeId AS "MediaTypeId",
                        MediaBucket AS "MediaBucket",
                        MediaExtension AS "MediaExtension"
                    FROM "Cases_DB"."MediaType"
                    WHERE MediaExtension = $1
                    """,
                    local_extension
                )

                if not type_record:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "status": "error",
                            "message": f"{UNSUPPORTED_EXTENSION_PREFIX}{local_extension}"
                        }
                    )

                media_typ_id = type_record["MediaTypeId"]
                bucket_name = type_record["MediaBucket"]
                db_extension = type_record["MediaExtension"] 

                # Hash the image for uniqueness
                media_hash = hashlib.sha256(file_bytes).hexdigest()

                # Checking for a duplicate
                existing_media = await connection.fetchrow(
                    """
                    SELECT MediaId AS "MediaId" 
                    FROM "Cases_DB"."Media" 
                    WHERE MediaHash = $1
                    """,
                    media_hash
                )

                if existing_media:
                    media_id = existing_media["MediaId"]
                    target_filename = f"{media_id}{db_extension}"

                    await connection.execute(
                        """
                        UPDATE "Cases_DB"."Cases"
                        SET evidence = array_append(
                            COALESCE(evidence, ARRAY[]::"Cases_DB".evidence_type[]),
                            ROW($2, $3)::"Cases_DB".evidence_type
                        )
                        WHERE CaseId = $1;
                        """,
                        case_id,
                        media_id,
                        filename
                    )

                else: # The hash is not in the db already therefore we need to add it
                    new_media_uuid = uuid.uuid4()

                    media_id = await connection.fetchval(
                        """
                        INSERT INTO "Cases_DB"."Media" (MediaId, MediaType, MediaHash)
                        VALUES ($1, $2, $3)
                        RETURNING MediaId
                        """,
                        new_media_uuid,
                        media_typ_id,
                        media_hash
                    )
                    target_filename = f"{media_id}{db_extension}"

                    storage_client = get_object()
                    await media.seek(0)
                    
                    file_stream = io.BytesIO(file_bytes)
                    storage_client.put_object(
                        Bucket=bucket_name,
                        Key=target_filename,
                        Body=file_stream,
                        ContentType=media.content_type
                    )

                    await connection.execute(
                        """
                        UPDATE "Cases_DB"."Cases"
                        SET evidence = array_append(
                            COALESCE(evidence, ARRAY[]::"Cases_DB".evidence_type[]),
                            ROW($2, $3)::"Cases_DB".evidence_type
                        )
                        WHERE CaseId = $1;
                        """,
                        case_id,
                        media_id,
                        filename
                    )

            # Creation of presigned URL below
            presign_client = get_object(for_presign=True)

            file_url = presign_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': target_filename
                },
                ExpiresIn=3600 
            )

            return {
                "MediaId": str(media_id),
                "Filename": filename,
                "url": file_url,
                "Status": "existing" if existing_media else "uploaded"
            }

        except asyncpg.UniqueViolationError:
            raise HTTPException(
                status_code=409, 
                detail={
                    "status": "error",
                    "message": MEDIA_ALREADY_ON_CASE
                }
            )

        except asyncpg.PostgresError as e:
            if "Duplicate evidence error" in str(e):
                raise HTTPException(
                    status_code=409,
                    detail={
                        "status": "error",
                        "message": MEDIA_ALREADY_ON_CASE
                    }
                )
            raise
        
        except HTTPException as e:
            raise e

        except (BotoCoreError, ClientError,EndpointConnectionError):
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": INTERNAL_SERVER_ERROR_STORAGE
                }
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": INTERNAL_SERVER_ERROR
                }
            )

        finally:
            await media.close()

    

    async def delete_evidence(
        self,
        media_id: uuid.UUID,
        connection: asyncpg.Connection,
        jwt_username: str = None,
        jwt_user_id: str | None = None,
        is_admin: bool = False,
    ):
        if self.case_id is None:
            raise HTTPException(
                status_code=400, 
                detail={
                    "status":"error",
                    "message":MISSING_CASE_ID
                }
            )

        try:
            async with connection.transaction():
                if jwt_user_id is not None:
                    await set_audit_executor(connection, jwt_user_id)

                if is_admin:
                    case_row = await connection.fetchrow(
                        """
                        UPDATE "Cases_DB"."Cases"
                        SET evidence = ARRAY(
                            SELECT elem
                            FROM unnest(COALESCE(evidence, ARRAY[]::"Cases_DB".evidence_type[])) AS elem
                            WHERE elem.evidence_id != $2
                        )
                        WHERE CaseId = $1
                            AND EXISTS (
                                SELECT 1
                                FROM unnest(COALESCE(evidence, ARRAY[]::"Cases_DB".evidence_type[])) AS elem
                                WHERE elem.evidence_id = $2
                            )
                        RETURNING CaseId
                        """,
                        self.case_id,
                        media_id,
                    )
                else:
                    case_row = await connection.fetchrow(
                        """
                        UPDATE "Cases_DB"."Cases"
                        SET evidence = ARRAY(
                            SELECT elem
                            FROM unnest(COALESCE(evidence, ARRAY[]::"Cases_DB".evidence_type[])) AS elem
                            WHERE elem.evidence_id != $2
                        )
                        WHERE CaseId = $1
                            AND CaseCreator = $3
                            AND CaseState = 'OPEN'
                            AND EXISTS (
                                SELECT 1
                                FROM unnest(COALESCE(evidence, ARRAY[]::"Cases_DB".evidence_type[])) AS elem
                                WHERE elem.evidence_id = $2
                            )
                        RETURNING CaseId
                        """,
                        self.case_id,
                        media_id,
                        jwt_username,
                    )

                if case_row is None:
                    raise HTTPException(
                        status_code=404 if is_admin else 403,
                        detail={
                            "status": "error",
                            "message": "Media not found." if is_admin else "Unauthorized to delete this evidence or record not found.",
                        },
                    )

                remaining_media_references = await connection.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM "Cases_DB"."Cases" other_case,
                         unnest(COALESCE(other_case.evidence, ARRAY[]::"Cases_DB".evidence_type[])) AS elem
                    WHERE elem.evidence_id = $1
                    """,
                    media_id,
                )

                deleted_media = None
                if remaining_media_references == 0:
                    deleted_media = await connection.fetchrow(
                        """
                        DELETE FROM "Cases_DB"."Media" media
                        USING "Cases_DB"."MediaType" media_type
                        WHERE media.MediaId = $1
                            AND media.MediaType = media_type.MediaTypeId
                        RETURNING media.MediaId AS mediaid,
                                  media_type.MediaBucket AS mediabucket,
                                  media_type.MediaExtension AS mediaextension
                        """,
                        media_id,
                    )

            if deleted_media is not None:
                storage_client = get_object()
                object_name = f"{deleted_media['mediaid']}{deleted_media['mediaextension']}"
                try:
                    await asyncio.to_thread(
                        storage_client.delete_object,
                        Bucket=deleted_media["mediabucket"],
                        Key=object_name,
                    )
                except Exception as e:
                    raise HTTPException(
                        status_code=500,
                        detail={
                            "status": "error",
                            "message": f"Failed to delete stored object {object_name}: {e}",
                        },
                    )
        
            return {
                "status" : "success",
                "deleted" : media_id
            }   
        except asyncpg.PostgresError:
            raise HTTPException(
                status_code=500, 
                detail={
                    "status":"error",
                    "message":"Database connection failure. Internal Server Error."
                }
            )

    def to_json(self):
        return {
            "caseId": str(self.case_id) if self.case_id is not None else None,
            "caseName": self.case_name,
            "caseCreator": self.case_creator,
            "caseDescription": self.case_description,
            "caseState": self.case_state,
            "caseAssigned": self.case_assigned,
            "caseCreationDate": self.case_creation_date.isoformat() if self.case_creation_date else None
        }

    async def get_comments(self, connection: asyncpg.Connection):
        if self.case_id is None:
            raise HTTPException(
                status_code=400, 
                detail=MISSING_CASE_ID
            )

        try:
            rows = await connection.fetch(
            """SELECT CommentID,
            Username, Comment, CommentTimestamp
            from "Cases_DB"."Comments" WHERE CaseId = $1""",
            self.case_id
        )

            return [dict(row) for row in rows]

        except asyncpg.PostgresError:
            raise HTTPException(
                status_code=500, 
                detail="Database connection failure. Internal Server Error."
            )

    async def add_comment(
        self, 
        connection: asyncpg.Connection, 
        username: str, 
        comment: str, 
        role: str,
        executor_id
    ) -> dict:
        if self.case_id is None:
            raise HTTPException(
                status_code=400, 
                detail=MISSING_CASE_ID
            )
        
        await set_audit_executor(connection, executor_id)

        row = await connection.fetchrow(
            """
            WITH case_check AS (
                SELECT caseid, casestate
                FROM "Cases_DB"."Cases"
                WHERE caseid = $1
            ),
            inserted AS (
                INSERT INTO "Cases_DB"."Comments" (caseid, username, comment)
                SELECT $1, $2, $3
                FROM case_check
                WHERE (
                    $4 = 'ADMIN'
                    OR ($4 = 'USER' AND casestate = 'CLOSED')
                    OR ($4 = 'INVESTIGATOR')
                )
                RETURNING commentid, caseid, username, comment, commenttimestamp
            )
            SELECT
                i.commentid,
                i.caseid,
                i.username,
                i.comment,
                i.commenttimestamp,
                c.casestate,
                (c.caseid IS NOT NULL) AS case_exists,
                (i.commentid IS NOT NULL) AS comment_inserted
            FROM case_check c
            LEFT JOIN inserted i ON true
            """,
            self.case_id,
            username,
            comment.strip(),
            role,
        )

        if row is None or not row["case_exists"]:
            raise HTTPException(
                status_code=404, 
                detail={
                    "status":"error",
                    "message":CASE_NOT_FOUND
                }
            )

        if not row["comment_inserted"]:
            if role == "USER":
                raise HTTPException(
                    status_code=403, 
                    detail={
                        "status":"error",
                        "message":"Users may only comment on closed cases"
                    }
                )
            raise HTTPException(
                status_code=403, 
                detail={
                    "status":"error",
                    "message":"Permission denied"
                }
            )

        return {
            "commentId": row["commentid"],
            "caseId": str(row["caseid"]),
            "username": row["username"],
            "comment": row["comment"],
            "timestamp": row["commenttimestamp"].isoformat() if row["commenttimestamp"] else None,
        }


    async def delete_case(
        self,
        username: str,
        is_admin: bool,
        connection: asyncpg.Connection,
        executor_id: str | None = None,
    ):
        if self.case_id is None:
            raise HTTPException(
                status_code=400,
                detail=MISSING_CASE_ID
            )

        case_id=self.case_id

        try:

            async with connection.transaction():
                if executor_id is not None:
                    await set_audit_executor(connection, executor_id)

                # An ADMIN may delete any case. Anyone else may only delete a case they created, and only while it is still OPEN.
                deleted_case = await connection.fetchrow(
                    """
                    DELETE FROM "Cases_DB"."Cases"
                    WHERE CaseId = $1
                        AND (
                            $2::boolean IS TRUE
                            OR (CaseCreator = $3 AND CaseState = 'OPEN')
                        )
                    RETURNING COALESCE(
                        evidence,
                        ARRAY[]::"Cases_DB".evidence_type[]
                    ) AS evidence
                    """,
                    case_id,
                    is_admin,
                    username
                )

                if deleted_case is None:
                    raise HTTPException(
                        status_code=404 if is_admin else 403,
                        detail={
                            "status": "error",
                            "message": CASE_NOT_FOUND if is_admin else CASE_DELETE_NOT_ALLOWED
                        }
                    )

                orphan_media = await collect_orphan_media(
                    connection,
                    deleted_case["evidence"]
                )

            await delete_stored_objects(orphan_media)

        except asyncpg.PostgresError:
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": DATABASE_ERROR_MESSAGE
                }
            )



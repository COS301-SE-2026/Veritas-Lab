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
minio_settings = Minio_Settings()
other_settings = Other_Settings()
r2_settings= R2_Settings()


async def set_audit_executor(connection: asyncpg.Connection, executor_id: str | uuid.UUID | None):
    if executor_id is None:
        return

    await connection.execute(
        "SELECT set_config('app.current_user_id', $1, true)",
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
        self.case_closed = False
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
        await connection.execute(f"SET app.current_user_id = '{user_id}';")
        row = await connection.fetchrow(
            """
            INSERT INTO "Cases_DB"."Cases"
            (casecreator, casename, casedescription, caseclosed)
            VALUES ($1, $2, $3, $4)
            RETURNING caseid, casecreationdate
            """,
            self.case_creator,
            self.case_name,
            self.case_description,
            self.case_closed
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
        file_bytes = await media.read()
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
                        INSERT INTO "Cases_DB"."Reports" (
                            CaseId, 
                            MediaId, 
                            ImageTitle, 
                            ReportArtifacts, 
                            ReportFindings, 
                            ReportComments
                        )
                        SELECT 
                            $1,
                            $2,
                            $3,
                            ReportArtifacts, 
                            ReportFindings, 
                            ReportComments
                        FROM "Cases_DB"."Reports"
                        WHERE MediaId = $2
                        LIMIT 1;
                        """,
                        case_id,
                        media_id,
                        filename
                    )

                else: 
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
                        INSERT INTO "Cases_DB"."Reports" (CaseId, MediaId, ImageTitle, ReportArtifacts, ReportFindings, ReportComments)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        case_id,
                        media_id,
                        filename,
                        None,
                        None,
                        None
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

                if jwt_username is not None:

                    status=await connection.execute(
                        """
                        DELETE FROM "Cases_DB"."Reports" r USING "Cases_DB"."Cases" c 
                        WHERE r.CaseId = c.CaseId
                            AND r.CaseId = $1
                            AND r.MediaId = $2
                            AND c.CaseCreator = $3;
                        """,
                        self.case_id,
                        media_id,
                        jwt_username
                    )

                    rows_deleted = int(status.split(" ")[1])

                    if rows_deleted == 0:
                        raise HTTPException(
                            status_code=403, 
                            detail={
                                "status":"error",
                                "message":"Unauthorized to delete this evidence or record not found."
                            }
                        )

        # Above this is the normal investigator deleting something
                else:
                    # This block contain the logic for the Admin deleting
                    status=await connection.execute(
                        """
                        DELETE FROM "Cases_DB"."Reports" r WHERE
                        r.CaseId = $1
                        AND r.MediaId = $2;
                        """,
                        self.case_id,
                        media_id
                    )

                    rows_deleted = int(status.split(" ")[1])
                    if rows_deleted == 0:
                        raise HTTPException(
                            status_code=404, 
                            detail={
                                "status":"error",
                                "message": "Media not found."
                            }
                        )

                deleted_media = await connection.fetchrow(
                    """
                    DELETE FROM "Cases_DB"."Media" media
                    USING "Cases_DB"."MediaType" mt
                    WHERE media.MediaId = $1
                    AND media.MediaType = mt.MediaTypeId
                    AND NOT EXISTS (
                        SELECT 1
                        FROM "Cases_DB"."Reports" r
                        WHERE r.MediaId = media.MediaId
                    )
                        RETURNING 
                        media.MediaId,
                        mt.MediaBucket,
                        mt.MediaExtension
                    """,
                        media_id
                    )

            if deleted_media is not None:
                    
                storage_client = get_object()

                object_name = f"{deleted_media['mediaid']}{deleted_media['mediaextension']}"

                try:
                    await asyncio.to_thread(
                        storage_client.delete_object,
                        Bucket=deleted_media["mediabucket"], 
                        Key=object_name
                    )
                    
                except HTTPException:
                    raise
                except Exception as e:
                    raise HTTPException(
                        status_code=500,
                        detail={
                            "status":"error",
                            "message":f"Failed to delete stored object {object_name}: {e}"
                        }
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
            "caseClosed": self.case_closed,
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
        
        await connection.execute(f"SET app.current_user_id = '{executor_id}';")

        row = await connection.fetchrow(
            """
            WITH case_check AS (
                SELECT caseid, caseclosed
                FROM "Cases_DB"."Cases"
                WHERE caseid = $1
            ),
            inserted AS (
                INSERT INTO "Cases_DB"."Comments" (caseid, username, comment)
                SELECT $1, $2, $3
                FROM case_check
                WHERE (
                    $4 = 'ADMIN'
                    OR ($4 = 'USER' AND caseclosed = TRUE)
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
                c.caseclosed,
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
        role: str,
        connection: asyncpg.Connection,
        executor_id: str | None = None,
    ):
        if self.case_id is None:
            raise HTTPException(
                status_code=400,
                detail=MISSING_CASE_ID
            )

        case_id=self.case_id
        
        orphan_media = []

        try:
            
            async with connection.transaction():
                if executor_id is not None:
                    await set_audit_executor(connection, executor_id)

                case_row = await connection.fetchrow(
                    """
                    SELECT casecreator
                    FROM "Cases_DB"."Cases"
                    WHERE caseid = $1
                    """,
                    case_id
                )

                if case_row is None:
                    raise HTTPException(
                        status_code=404,
                        detail={
                            "status": "error",
                            "message": CASE_NOT_FOUND
                        }
                    )
                
                case_creator = case_row["casecreator"]

                if role != "ADMIN" and username != case_creator:
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "status": "error",
                            "message": "Only the case creator or an admin can delete this case"
                        }
                    )

                result = await connection.fetchrow(
                    """
                    WITH target_media AS (
                        SELECT COALESCE(array_agg(DISTINCT MediaId), '{}') AS mediaids
                        FROM "Cases_DB"."Reports"
                        WHERE CaseId = $1
                    ),
                    deleted_case AS (
                        DELETE FROM "Cases_DB"."Cases"
                        WHERE CaseId = $1
                        RETURNING CaseId AS caseid
                    )
                    SELECT d.caseid, m.mediaids
                    FROM deleted_case d
                    CROSS JOIN target_media m
                    """,
                    case_id
                )

                # returned caseid only serves for deleteion detection.
                if result is None:
                    raise HTTPException(
                        status_code=404,
                        detail={
                            "status": "error",
                            "message": CASE_NOT_FOUND
                        }
                    )
                
                media_rows = result["mediaids"]
            
                for media_id in media_rows:

                    deleted_media = await connection.fetchrow(
                        """
                        DELETE FROM "Cases_DB"."Media" media
                        USING "Cases_DB"."MediaType" mt
                        WHERE media.MediaId = $1
                        AND media.MediaType = mt.MediaTypeId
                        AND NOT EXISTS (
                            SELECT 1
                            FROM "Cases_DB"."Reports" r
                            WHERE r.MediaId = media.MediaId
                        )
                        RETURNING 
                            media.MediaId AS "mediaid",
                            mt.MediaBucket AS "mediabucket",
                            mt.MediaExtension AS "mediaextension"
                        """,
                        media_id
                    )

                    if deleted_media is not None:
                        orphan_media.append({
                            "mediaid": deleted_media["mediaid"],
                            "mediabucket": deleted_media["mediabucket"],
                            "mediaextension": deleted_media["mediaextension"]
                        })                 
                
            storage_client = get_object()

            for media in orphan_media:
                object_name = f"{media['mediaid']}{media['mediaextension']}"

                try:
                    #$414
                    storage_client.delete_object(
                        Bucket=media["mediabucket"], 
                        Key=object_name
                    )
                except HTTPException:
                    raise
                except Exception:
                    raise HTTPException(
                        status_code=500,
                        detail="Object storage Error"
                    )

        except asyncpg.PostgresError:
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": "Database error"
                }
            )



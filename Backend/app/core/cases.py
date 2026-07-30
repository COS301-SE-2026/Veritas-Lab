import uuid
from uuid import uuid4
import json
from app.core.env import ENVLoader, IS_PROD
import asyncpg
import asyncio
import os
import io
import hashlib
from dotenv import load_dotenv
from fastapi import UploadFile, HTTPException
from pathlib import Path
from pypdf import PdfReader
from datetime import datetime, timedelta, timezone
import boto3
from botocore.client import Config
from mypy_boto3_s3 import S3Client


load_dotenv()
env = ENVLoader()

DB_USER = env.getRequiredEnv("DB_USER")
DB_PASSWORD = env.getRequiredEnv("DB_PASSWORD")
DB_HOST = env.getRequiredEnv("DB_HOST")
DB_PORT = env.getRequiredIntEnv("DB_PORT")
DB_NAME = env.getRequiredEnv("DB_NAME")
DB_SSL = env.getRequiredEnv("DB_SSL").strip().lower() in ("1", "true")

MISSING_CASE_ID = "Case id is missing"

async def get_connection() -> asyncpg.Connection:
    return await asyncpg.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT,
        ssl="require" if DB_SSL else None,
    )

def get_object(for_presign: bool = False) -> S3Client:
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
                s3={
                    "addressing_style": "path"
                }
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
                s3={
                    "addressing_style": "path"
                }
            ),
        )

# If the case_id is None then the case is not in the db. You may call create().
# When the case_id is not None then we know the case exists in the db. Time and Id is adjusted after create() is called.
class Case:
    def __init__(
        self, 
        CaseCreator: str = None, 
        CaseName: str = None, 
        CaseDescription: str=None, 
        CaseID: str=None
    ):
        if  (CaseCreator is not None):
            if not CaseCreator.strip():
                raise ValueError("CaseCreator is required")
            if  len(CaseCreator) > 100:
                raise ValueError("Name is too long. Must be 100 characters or less")
        if  (CaseName is not None):
            if not CaseName.strip():
                raise ValueError("CaseName is required")
            if len(CaseName) > 255:
                raise ValueError("CaseName must be 255 characters or less")
        
        self.CaseCreator = None if CaseCreator is None else CaseCreator.strip()
        self.CaseName = None if CaseName is None else CaseName.strip()
        self.CaseDescription = CaseDescription
        self.CaseClosed = False
        if CaseID is not None:
            cleaned_id = CaseID.strip()
            try:
                uuid.UUID(cleaned_id)
                self.CaseId = cleaned_id
            except ValueError:
                raise ValueError(f"'{CaseID}' is not a valid UUID format")
        else:
            self.CaseId = None
        self.CaseCreationDate = None

    async def create(self):
        if self.CaseId is not None:
            raise ValueError("This case already exists")
        
        connection = await get_connection()

        try:
            row = await connection.fetchrow(
                """
                INSERT INTO "Cases_DB"."Cases"
                (casecreator, casename, casedescription, caseclosed)
                VALUES ($1, $2, $3, $4)
                RETURNING caseid, casecreationdate
                """,
                self.CaseCreator,
                self.CaseName,
                self.CaseDescription,
                self.CaseClosed
            )

            self.CaseId=row["caseid"]
            self.CaseCreationDate=row["casecreationdate"]
            return str(row["caseid"])

        finally:
            await connection.close()

    async def add_evidence(self, media: UploadFile, case_id: uuid.UUID):
        filename = media.filename
        localExtension = Path(filename).suffix.lower() #extract of the extension (e.g: .png)
        fileBytes = await media.read()
        await media.seek(0)
        #script detection
        if localExtension == ".pdf":

            try:
                pdfFile = io.BytesIO(fileBytes)
                reader = PdfReader(pdfFile)

                try: 
                    root = reader.trailer.get("/Root", {}) #checcking for automatic triggers
                    if root:
                        root = root.get_object()
                        if "/OpenAction" in root or "/AA" in root:
                            raise HTTPException(
                                status_code=400, 
                                detail="We don't allow scripts in pdfs. They are a security concern."
                            )

                        if "/Names" in root:
                            names=root["/Names"].get_object()
                            if "/JavaScript" in names:
                                raise HTTPException(
                                        status_code=400,
                                        detail="We don't allow scripts in pdfs. They are a security concern."
                                    )
                except HTTPException:
                    raise
                except KeyError :
                    pass
                except Exception :
                    raise HTTPException(
                        status_code=400,
                        detail="Could not verify PDF security. File rejected."
                    )  
                     
            except HTTPException:
                raise 
            except Exception as e:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid or corrupted PDF file: {str(e)}"
                )
        # validate case_id is a UUID
        try:
            case_uuid = uuid.UUID(str(case_id)) if not isinstance(case_id, uuid.UUID) else case_id
        except Exception:
            raise HTTPException(
                status_code=400, 
                detail="Invalid case_id UUID"
            )

        connection = await get_connection()

        try:
            typeRecord = await connection.fetchrow(
                """
                SELECT 
                    MediaTypeId AS "MediaTypeId",
                    MediaBucket AS "MediaBucket",
                    MediaExtension AS "MediaExtension"
                    FROM "Cases_DB"."MediaType"
                WHERE MediaExtension = $1
                """,
                localExtension
            )

            if not typeRecord:
                raise HTTPException(status_code=400, detail=f"Unsupported file extension: {localExtension}")

            mediaTypeId = typeRecord["MediaTypeId"]
            bucketName = typeRecord["MediaBucket"]
            dbExtension = typeRecord["MediaExtension"] 
            
                #Hash the image for uniqueness
            mediaHash = hashlib.sha256(fileBytes).hexdigest()

            storage_client = get_object()

            
            #checking for a duplicate
            existingMedia = await connection.fetchrow(
                """
                SELECT MediaId  AS "MediaId" 
                FROM "Cases_DB"."Media" 
                WHERE MediaHash = $1
                """,
                mediaHash
            )

            if existingMedia:
                mediaId=existingMedia["MediaId"]
                targetFilename = f"{mediaId}{dbExtension}"
                # Need to reproduce the same db report for this case.

                try:
                    # Insert into the Reports table allowing the report to have the image's name in the image title column

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
                        case_uuid,
                        mediaId,
                        filename
                    )

                except asyncpg.UniqueViolationError:
                    raise HTTPException(
                        status_code=409, 
                        detail="Image already associated with this case"
                    )
                except Exception:
                    pass
            else: 
                newMediaUuid = uuid.uuid4()

                mediaId = await connection.fetchval(
                    """
                    INSERT INTO "Cases_DB"."Media" (MediaId, MediaType, MediaHash)
                    VALUES ($1, $2, $3)
                    RETURNING MediaId
                    """,
                    newMediaUuid,
                    mediaTypeId,
                    mediaHash
                )
                targetFilename = f"{mediaId}{dbExtension}"

                await media.seek(0)
                
                fileStream = io.BytesIO(fileBytes)
                storage_client.put_object(
                    Bucket=bucketName,
                    Key=targetFilename,
                    Body=fileStream,
                    ContentType=media.content_type
                )

                try:
                    # Insesrt into the Reports table allowing the report to have the image's name in the image title column

                    await connection.execute(
                        """
                        INSERT INTO "Cases_DB"."Reports" (CaseId, MediaId, ImageTitle, ReportArtifacts, ReportFindings, ReportComments)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        case_uuid,
                        mediaId,
                        filename,
                        None,
                        None,
                        None
                    )

                except asyncpg.UniqueViolationError:
                    raise HTTPException(
                        status_code=409, 
                        detail="Image already associated with this case"
                    )
                except Exception:
                    pass

            #Creation of presigned URL below
            presign_client = get_object(for_presign=True)# function to get the client until we do the pools

            fileUrl = presign_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucketName,
                    'Key': targetFilename
                },
                ExpiresIn=3600 
            )

            return{
                "MediaId": str(mediaId),
                "Filename": filename,
                "url": fileUrl,
                "Status": "existing" if existingMedia else "uploaded"
            }
        
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Internal Server Error: {str(e)}"
                )

        finally:
            await connection.close()
            await media.close()

    async def delete_evidence(self, media_id: uuid.UUID, JWT_username: str = None):
        if self.CaseId is None:
            raise HTTPException(
                status_code=400, 
                detail=MISSING_CASE_ID
            )

        connection = None

        try:
            connection=await get_connection()

            if JWT_username is not None:

                status=await connection.execute(
                    """
                    DELETE FROM "Cases_DB"."Reports" r USING "Cases_DB"."Cases" c WHERE r."CaseId" = c."CaseId"
                    AND r."CaseId" = $1
                    AND r."MediaId" = $2
                    AND c."CaseCreator" = $3;
                    """,
                    self.CaseId,
                    media_id,
                    JWT_username
                )

                rows_deleted = int(status.split(" ")[1])
                if rows_deleted == 0:
                    raise HTTPException(
                        status_code=403, 
                        detail="Unauthorized to delete this evidence or record not found."
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
                            media.MediaId AS "mediaid",
                            mt.MediaBucket AS "mediabucket",
                            mt.MediaExtension AS "mediaextension"
                        """,
                        media_id
                    )

                if deleted_media is not None:
                    

                    storage_client = get_object()

                    object_name = f"{deleted_media['mediaid']}{deleted_media['mediaextension']}"

                    try:
                        storage_client.delete_object(
                            Bucket=deleted_media["mediabucket"], 
                            Key=object_name
                        )
                        
                    except Exception as e:
                        print(f"Failed to delete stored object {object_name}: {e}")
        # Above this is the normal investigator deleting something
            else:
                # This block contain the logic for the Admin deleting
                status=await connection.execute(
                    """
                    DELETE FROM "Cases_DB"."Reports" r WHERE
                    r."CaseId" = $1
                    AND r."MediaId" = $2;
                    """,
                    self.CaseId,
                    media_id
                )

                rows_deleted = int(status.split(" ")[1])
                if rows_deleted == 0:
                    raise HTTPException(
                        status_code=404, 
                        detail="Media not found."
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
                            media.MediaId AS "mediaid",
                            mt.MediaBucket AS "mediabucket",
                            mt.MediaExtension AS "mediaextension"
                        """,
                        media_id
                    )

                if deleted_media is not None:
                    
                    storage_client = get_object()

                    object_name = f"{deleted_media['mediaid']}{deleted_media['mediaextension']}"

                    try:
                        storage_client.delete_object(
                            Bucket=deleted_media["mediabucket"], 
                            Key=object_name
                        )
                        
                        
                    except Exception as e:
                        print(f"Failed to delete stored object {object_name}: {e}")
        
            return {
                "Status" : "success",
                "Deleted" : media_id
            }   
        except asyncpg.PostgresError:
            raise HTTPException(
                status_code=500, 
                detail="Database connection failure. Internal Server Error."
            )

        finally:
            if connection is not None:
                await connection.close()
        

    def to_json(self):
        return {
            "caseId": str(self.CaseId) if self.CaseId is not None else None,
            "caseName": self.CaseName,
            "caseCreator": self.CaseCreator,
            "caseDescription": self.CaseDescription,
            "caseClosed": self.CaseClosed,
            "caseCreationDate": self.CaseCreationDate.isoformat() if self.CaseCreationDate else None
        }

    async def get_comments(self):
        if self.CaseId is None:
            raise HTTPException(
                status_code=400, 
                detail=MISSING_CASE_ID
            )

        connection = None
        try:
            connection = await get_connection()

            rows = await connection.fetch(
            """SELECT CommentID, Username, Comment, CommentTimestamp from "Cases_DB"."Comments" WHERE CaseId = $1"""
            , self.CaseId
        )

            return [dict(row) for row in rows]

        except asyncpg.PostgresError:
            raise HTTPException(
                status_code=500, 
                detail="Database connection failure. Internal Server Error."
            )

        finally:
            if connection is not None:
                await connection.close()

    @staticmethod
    def validate_comment_length(comment: str) -> bool:
        if not isinstance(comment, str):
            return False
        return len(comment.strip()) > 0

    async def add_comment(
        self, 
        connection: asyncpg.Connection, 
        username: str, 
        comment: str, 
        role: str
    ) -> dict:
        if self.CaseId is None:
            raise HTTPException(
                status_code=400, 
                detail=MISSING_CASE_ID
            )

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
            self.CaseId,
            username,
            comment.strip(),
            role,
        )

        if row is None or not row["case_exists"]:
            raise HTTPException(
                status_code=404, 
                detail="Case not found"
            )

        if not row["comment_inserted"]:
            if role == "USER":
                raise HTTPException(
                    status_code=403, 
                    detail="Users may only comment on closed cases"
                )
            raise HTTPException(
                status_code=403, 
                detail="Permission denied"
            )

        return {
            "commentId": row["commentid"],
            "caseId": str(row["caseid"]),
            "username": row["username"],
            "comment": row["comment"],
            "timestamp": row["commenttimestamp"].isoformat() if row["commenttimestamp"] else None,
        }

    @staticmethod
    async def delete_case(
        case_id: uuid.UUID, 
        username: str, 
        role: str
    ):
        connection = await get_connection()

        orphan_media = []

        try:
            async with connection.transaction():
                case_row = await connection.fetchrow(
                    """
                    SELECT casecreator
                    FROM "Cases_DB"."Cases"
                    WHERE caseid = $1
                    """,
                    case_id
                )

                if case_row is None:
                    return {
                        "deleted": False,
                        "reason": "not_found"
                    }
                
                case_creator = case_row["casecreator"]

                if role != "ADMIN" and username != case_creator:
                    return {
                        "deleted": False,
                        "reason": "unauthorized"
                    }

                media_rows = await connection.fetch(
                    """
                    SELECT DISTINCT MediaId AS "mediaid"
                    FROM "Cases_DB"."Reports"
                    WHERE CaseId = $1
                    """,
                    case_id
                )

                deleted_case = await connection.fetchrow(
                    """
                    DELETE FROM "Cases_DB"."Cases"
                    WHERE caseid = $1
                    RETURNING caseid
                    """,
                    case_id
                )

                if deleted_case is None:
                    return {
                        "deleted": False,
                        "reason": "not_found"
                    }
            
                for media_row in media_rows:
                    media_id = media_row["mediaid"]

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
                    storage_client.head_object(
                        Bucket=media["mediabucket"], 
                        Key=object_name
                    )
                except Exception as e:
                    print(f"Failed to delete stored object {object_name}: {e}")

            return {
                "deleted": True,
                "reason": "deleted"
            }
        finally:
            await connection.close()


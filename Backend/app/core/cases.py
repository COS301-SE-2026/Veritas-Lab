import uuid
from uuid import uuid4
import json
from app.core.env import ENVLoader
import asyncpg
import asyncio
import os
import io
import hashlib
from dotenv import load_dotenv
from fastapi import UploadFile, HTTPException
from pathlib import Path
from minio import Minio
from pypdf import PdfReader
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

load_dotenv()
env = ENVLoader()

DB_USER = env.getRequiredEnv("DB_USER")
DB_PASSWORD = env.getRequiredEnv("DB_PASSWORD")
DB_HOST = env.getRequiredEnv("DB_HOST")
DB_PORT = env.getRequiredIntEnv("DB_PORT")
DB_NAME = env.getRequiredEnv("DB_NAME")
DB_SSL = env.getRequiredEnv("DB_SSL").strip().lower() in ("1", "true")

_MISSING_CASE_ID = "Case id is missing"

async def getConnection() -> asyncpg.Connection:
    return await asyncpg.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT,
        ssl="require" if DB_SSL else None,
    )

# If the case_id is None then the case is not in the db. You may call create().
# When the case_id is not None then we know the case exists in the db. Time and Id is adjusted after create() is called.
class Case:
    def __init__(self, CaseCreator: str = None, CaseName: str = None, CaseDescription: str=None, CaseID: str=None):
        if  not (CaseCreator is None):
            if not CaseCreator.strip():
                raise ValueError("CaseCreator is required")
            if  len(CaseCreator) > 100:
                raise ValueError("Name is too long. Must be 100 characters or less")
        if not (CaseName is None):
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
        
        connection = await getConnection()

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

    async def addEvidence(self, media: UploadFile, case_id: uuid.UUID):
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
                except KeyError as k_err:
                    pass
                except Exception as scan_err:
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
            raise HTTPException(status_code=400, detail="Invalid case_id UUID")

        connection = await getConnection()

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

            minioEndpointRaw = (
                os.getenv("MINIO_ENDPOINT")
                or os.getenv("AWS_S3_ENDPOINT_URL")
                or "localhost:9000"
            )
            minioSecure = minioEndpointRaw.startswith("https://")
            minioEndpoint = minioEndpointRaw.removeprefix("http://").removeprefix("https://")
            minioClient = Minio(
                minioEndpoint,
                access_key=os.getenv("MINIO_ACCESS_KEY") or os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
                secret_key=os.getenv("MINIO_SECRET_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
                secure=minioSecure
            )

            
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
                            ImageId, 
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
                        WHERE ImageId = $2
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
                minioClient.put_object(
                    bucket_name=bucketName,
                    object_name=targetFilename,
                    data=fileStream,
                    length=len(fileBytes),
                    content_type=media.content_type
                )  

                try:
                    # Insesrt into the Reports table allowing the report to have the image's name in the image title column

                    await connection.execute(
                        """
                        INSERT INTO "Cases_DB"."Reports" (CaseId, ImageId, ImageTitle, ReportArtifacts, ReportFindings, ReportComments)
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

            fileUrl = presign_client.presigned_get_object(
                bucket_name=bucketName,
                object_name=targetFilename,
                expires=timedelta(hours=1)
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

    async def deleteEvidence(self, media_id: uuid.UUID, JWT_username: str = None):
        if self.CaseId is None:
            raise HTTPException(status_code=400, detail=_MISSING_CASE_ID)

        connection = None

        try:
            connection=await asyncpg.connect(
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                host=DB_HOST,
                port=DB_PORT
            )

            if JWT_username is not None:

                status=await connection.execute(
                    """
                    DELETE FROM "Cases_DB"."Reports" r USING "Cases_DB"."Cases" c WHERE r."CaseId" = c."CaseId"
                    AND r."CaseId" = $1
                    AND r."ImageId" = $2
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
                            WHERE r.ImageId = media.MediaId
                        )
                        RETURNING 
                            media.MediaId AS "mediaid",
                            mt.MediaBucket AS "mediabucket",
                            mt.MediaExtension AS "mediaextension"
                        """,
                        media_id
                    )

                if deleted_media is not None:
                    
                    minioEndpointRaw = (
                        os.getenv("MINIO_ENDPOINT")
                        or os.getenv("AWS_S3_ENDPOINT_URL")
                        or "localhost:9000"
                    )

                    minioSecure = minioEndpointRaw.startswith("https://")
                    minioEndpoint = minioEndpointRaw.removeprefix("http://").removeprefix("https://")

                    minioClient = Minio(
                        minioEndpoint,
                        access_key=os.getenv("MINIO_ACCESS_KEY") or os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
                        secret_key=os.getenv("MINIO_SECRET_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
                        secure=minioSecure
                    )

                    object_name = f"{deleted_media['mediaid']}{deleted_media['mediaextension']}"

                    try:
                        minioClient.remove_object(
                            bucket_name=deleted_media["mediabucket"],
                            object_name=object_name
                        )
                    except Exception as e:
                        print(f"Failed to delete MinIO object {object_name}: {e}")
        # Above this is the normal investigator deleting something
            else:
                # This block contain the logic for the Admin deleting
                status=await connection.execute(
                    """
                    DELETE FROM "Cases_DB"."Reports" r WHERE
                    r."CaseId" = $1
                    AND r."ImageId" = $2;
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
                            WHERE r.ImageId = media.MediaId
                        )
                        RETURNING 
                            media.MediaId AS "mediaid",
                            mt.MediaBucket AS "mediabucket",
                            mt.MediaExtension AS "mediaextension"
                        """,
                        media_id
                    )

                if deleted_media is not None:
                    
                    minioEndpointRaw = (
                        os.getenv("MINIO_ENDPOINT")
                        or os.getenv("AWS_S3_ENDPOINT_URL")
                        or "localhost:9000"
                    )

                    minioSecure = minioEndpointRaw.startswith("https://")
                    minioEndpoint = minioEndpointRaw.removeprefix("http://").removeprefix("https://")

                    minioClient = Minio(
                        minioEndpoint,
                        access_key=os.getenv("MINIO_ACCESS_KEY") or os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
                        secret_key=os.getenv("MINIO_SECRET_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
                        secure=minioSecure
                    )

                    object_name = f"{deleted_media['mediaid']}{deleted_media['mediaextension']}"

                    try:
                        minioClient.remove_object(
                            bucket_name=deleted_media["mediabucket"],
                            object_name=object_name
                        )
                    except Exception as e:
                        print(f"Failed to delete MinIO object {object_name}: {e}")
        
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
        

    def toJSON(self):
        return {
            "caseId": str(self.CaseId) if self.CaseId is not None else None,
            "caseName": self.CaseName,
            "caseCreator": self.CaseCreator,
            "caseDescription": self.CaseDescription,
            "caseClosed": self.CaseClosed,
            "caseCreationDate": self.CaseCreationDate.isoformat() if self.CaseCreationDate else None
        }

    async def getComments(self):
        if self.CaseId is None:
            raise HTTPException(status_code=400, detail=_MISSING_CASE_ID)

        connection = None
        try:
            connection = await getConnection()

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
    def validateCommentLength(comment: str) -> bool:
        if not isinstance(comment, str):
            return False
        return len(comment.strip()) > 0

    async def addComment(self, connection: asyncpg.Connection, username: str, comment: str, role: str) -> dict:
        if self.CaseId is None:
            raise HTTPException(status_code=400, detail=_MISSING_CASE_ID)

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
                    OR ($4 = 'INVESTIGATOR' AND caseclosed = FALSE)
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
            raise HTTPException(status_code=404, detail="Case not found")

        if not row["comment_inserted"]:
            if role == "USER":
                raise HTTPException(status_code=403, detail="Users may only comment on closed cases")
            if role == "INVESTIGATOR":
                raise HTTPException(status_code=403, detail="Investigators may only comment on open cases")
            raise HTTPException(status_code=403, detail="Permission denied")

        return {
            "commentId": row["commentid"],
            "caseId": str(row["caseid"]),
            "username": row["username"],
            "comment": row["comment"],
            "timestamp": row["commenttimestamp"].isoformat() if row["commenttimestamp"] else None,
        }

    @staticmethod
    async def deleteCase(case_id: uuid.UUID, username: str, role: str):
        connection = await getConnection()

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
                    SELECT DISTINCT ImageId AS "mediaid"
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
                            WHERE r.ImageId = media.MediaId
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
                
            minioEndpointRaw = (
                os.getenv("MINIO_ENDPOINT")
                or os.getenv("AWS_S3_ENDPOINT_URL")
                or "localhost:9000"
            )

            minioSecure = minioEndpointRaw.startswith("https://")
            minioEndpoint = minioEndpointRaw.removeprefix("http://").removeprefix("https://")

            minioClient = Minio(
                minioEndpoint,
                access_key=os.getenv("MINIO_ACCESS_KEY") or os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
                secret_key=os.getenv("MINIO_SECRET_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
                secure=minioSecure
            )

            for media in orphan_media:
                object_name = f"{media['mediaid']}{media['mediaextension']}"

                try:
                    minioClient.remove_object(
                        bucket_name=media["mediabucket"],
                        object_name=object_name
                    )
                except Exception as e:
                    print(f"Failed to delete MinIO object {object_name}: {e}")

            return {
                "deleted": True,
                "reason": "deleted"
            }
        finally:
            await connection.close()


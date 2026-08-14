import uuid
from uuid import uuid4
import asyncpg
import io
import hashlib
from fastapi import UploadFile, HTTPException
from pathlib import Path
from pypdf import PdfReader
from datetime import datetime, timedelta, timezone
import boto3
from botocore.client import Config
from app.core.env import Postgres_Settings, Other_Settings, Minio_Settings, R2_Settings
from mypy_boto3_s3 import S3Client

CASE_NOT_FOUND="Case not found"
MISSING_CASE_ID = "Case id is missing"
postgres_settings = Postgres_Settings()
minio_settings = Minio_Settings()
other_settings = Other_Settings()
r2_settings= R2_Settings()

async def get_connection() -> asyncpg.Connection:
    return await asyncpg.connect(
        user=postgres_settings.DB_USER,
        password=postgres_settings.DB_PASSWORD,
        database=postgres_settings.DB_NAME,
        host=postgres_settings.DB_HOST,
        port=postgres_settings.DB_PORT,
        ssl="require" if postgres_settings.DB_SSL else None,
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
            if not case_creator.strip():
                raise ValueError("CaseCreator is required")
            if  len(case_creator) > 100:
                raise ValueError("Name is too long. Must be 100 characters or less")
        if  (case_name is not None):
            if not case_name.strip():
                raise ValueError("CaseName is required")
            if len(case_name) > 255:
                raise ValueError("CaseName must be 255 characters or less")
        
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

    async def create(self):
        if self.case_id  is not None:
            raise HTTPException(
                status_code=409,
                detail={
                    "status": "error",
                    "message": "This case already exists"
                }
            )
        
        connection = await get_connection()

        try:
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
        if self.case_id is None:
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
                    self.case_id,
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
                    self.case_id,
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
            "caseId": str(self.case_id) if self.case_id is not None else None,
            "caseName": self.case_name,
            "caseCreator": self.case_creator,
            "caseDescription": self.case_description,
            "caseClosed": self.case_closed,
            "caseCreationDate": self.case_creation_date.isoformat() if self.case_creation_date else None
        }

    async def get_comments(self):
        if self.case_id is None:
            raise HTTPException(
                status_code=400, 
                detail=MISSING_CASE_ID
            )

        connection = None
        try:
            connection = await get_connection()

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

        finally:
            if connection is not None:
                await connection.close()

    async def add_comment(
        self, 
        connection: asyncpg.Connection, 
        username: str, 
        comment: str, 
        role: str
    ) -> dict:
        if self.case_id is None:
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
        role: str
    ):
        if self.case_id is None:
            raise HTTPException(
                status_code=400,
                detail=MISSING_CASE_ID
            )

        case_id=self.case_id
        
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
                except Exception:
                    raise HTTPException(
                        status_code=500,
                        detail="Object storage Error"
                    )

        finally:
            await connection.close()


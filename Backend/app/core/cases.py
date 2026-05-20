import uuid
from uuid import uuid4
from datetime import datetime, timezone
import asyncpg
import asyncio
import os
import hashlib
from dotenv import load_dotenv
from fastapi import UploadFile, HTTPException
from pathlib import Path
from minio import Minio

load_dotenv()

class Case:
    def __init__(self, CaseCreator: str = None, CaseName: str = None, CaseReviews: dict = None):
        if not CaseCreator:
            raise ValueError("CaseCreator is required")
        if not CaseName:
            raise ValueError("CaseName is required")
        if len(CaseName) > 255:
            raise ValueError("CaseName must be 255 characters or less")
        if len(CaseCreator) > 100:
            raise ValueError("Name is too long. Must be 100 characters or less")

        self.CaseId = uuid4()
        self.CaseCreator = CaseCreator
        self.CaseName = CaseName
        self.CaseReviews = CaseReviews
        self.CaseCreationDate = datetime.now(timezone.utc)

    async def save(self):
        connection = await asyncpg.connect(
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", ""),
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432))
        )

        case_id = await connection.fetchval(
            """
            INSERT INTO "Cases_DB"."Cases" ("CaseId", "CaseCreator", "CaseName", "CaseReviews", "CaseCreationDate")
            VALUES ($1, $2, $3, $4, $5)
            RETURNING "CaseId"
            """,
            self.CaseId,
            self.CaseCreator,
            self.CaseName,
            self.CaseReviews,
            self.CaseCreationDate
        )

        await connection.close()

        return str(case_id)

    async def addEvidence(self,media: UploadFile):
        filename = media.filename
        localExtension = Path(filename).suffix.lower() #extract of the extension (e.g: .png)

        connection = await asyncpg.connect(
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", ""),
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432))
        )

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
            fileBytes = await media.read()
            mediaHash = hashlib.sha256(fileBytes).hexdigest()

            

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
                # Allow the dupe we just won't save it
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

                minioEndpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
                minioClient = Minio(
                    minioEndpoint,
                    access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
                    secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
                    secure=False
                )
                
                minioClient.put_object(
                    bucket_name=bucketName,
                    object_name=targetFilename,
                    data=media.file,
                    length=len(fileBytes),
                    content_type=media.content_type
                )  

            minioDomain = os.getenv("MINIO_EXTERNAL_URL", "http://localhost:9000")
            fileUrl = f"{minioDomain}/{bucketName}/{targetFilename}"

            return{
                "MediaId": str(mediaId),
                "url": fileUrl,
                "Status": "existing" if existingMedia else "uploaded"
            }

        finally:
            await connection.close()
            await media.close()

import uuid
from uuid import uuid4
import json
from app.core.env import ENVLoader
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
env = ENVLoader()

DB_USER = env.getRequiredEnv("DB_USER")
DB_PASSWORD = env.getRequiredEnv("DB_PASSWORD")
DB_HOST = env.getRequiredEnv("DB_HOST")
DB_PORT = env.getRequiredIntEnv("DB_PORT")
DB_NAME = env.getRequiredEnv("DB_NAME")

# If the CaseId is None then the case is not in the db. You may call create().
# When the CaseId is not None then we know the case exists in the db. Time and Id is adjusted after create() is called.

class Case:
    def __init__(self, CaseCreator: str = None, CaseName: str = None, CaseReviews: dict = None, CaseDescription: str=None):
        if not CaseCreator or not CaseCreator.strip():
            raise ValueError("CaseCreator is required")
        if not CaseName or not CaseName.strip():
            raise ValueError("CaseName is required")
        if len(CaseName) > 255:
            raise ValueError("CaseName must be 255 characters or less")
        if len(CaseCreator) > 100:
            raise ValueError("Name is too long. Must be 100 characters or less")

        self.CaseCreator = CaseCreator.strip()
        self.CaseName = CaseName.strip()
        self.CaseReviews = CaseReviews
        self.CaseDescription = CaseDescription
        self.CaseClosed = False
        self.CaseId = None
        self.CaseCreationDate = None

    async def create(self):
        if self.CaseId is not None:
            raise ValueError("This case already exists")
        
        connection = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT
        )

        try:
            row = await connection.fetchrow(
                """
                INSERT INTO "Cases_DB"."Cases"
                (casecreator, casename, casereviews, casedescription, caseclosed)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING caseid, casecreationdate
                """,
                self.CaseCreator,
                self.CaseName,
                json.dumps(self.CaseReviews) if self.CaseReviews is not None else None,
                self.CaseDescription,
                self.CaseClosed
            )

            self.CaseId=row["caseid"]
            self.CaseCreationDate=row["casecreationdate"]
            return str(row["caseid"])

        finally:
            await connection.close()

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

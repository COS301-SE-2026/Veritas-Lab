from abc import ABC, abstractmethod
from uuid import UUID
import asyncpg
from dotenv import load_dotenv
import exiftool
from app.core.env import ENVLoader
from minio import Minio
import os
import json
import tempfile
from starlette.concurrency import run_in_threadpool

load_dotenv()
env = ENVLoader()

DB_USER = env.getRequiredEnv("DB_USER")
DB_PASSWORD = env.getRequiredEnv("DB_PASSWORD")
DB_HOST = env.getRequiredEnv("DB_HOST")
DB_PORT = env.getRequiredIntEnv("DB_PORT")
DB_NAME = env.getRequiredEnv("DB_NAME")

class MediaService(ABC):

    async def extract(self, file_path: str, media_record: dict):
        with exiftool.ExifToolHelper() as et:
            metadata_list = et.get_metadata(file_path)

        metadata = metadata_list[0] if metadata_list else {}

        return {
            "media_id": str(media_record["media_id"]),
            "file_type": media_record["extension"].replace(".","").upper(),
            "bucket": media_record["bucket"],
            "object_name": media_record["object_name"],
            "metadata": metadata
        }
    
    async def getMediaRecord(self, media_id: UUID):
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
                SELECT
                    media.MediaId AS "mediaid",
                    mt.MediaBucket AS "mediabucket",
                    mt.MediaExtension AS "mediaextension"
                FROM "Cases_DB"."Media" media
                JOIN "Cases_DB"."MediaType" mt
                    ON media.MediaType = mt.MediaTypeId
                WHERE media.MediaId = $1
                """,
                media_id
            )

            if row is None:
                raise ValueError("Media not found")
            
            return {
                "media_id": row["mediaid"],
                "bucket": row["mediabucket"],
                "extension": row["mediaextension"],
                "object_name": f"{row['mediaid']}{row['mediaextension']}"
            }
        
        finally:
            await connection.close()

    async def downloadMedia(self, media_record: dict, file_path: str):
        minio_client = self.createMinioClient()

        await run_in_threadpool(
            minio_client.fget_object,
            bucket_name=media_record["bucket"],
            object_name=media_record["object_name"],
            file_path=file_path
        )
    
    def createMinioClient(self):
        minio_endpoint_raw = (
            os.getenv("MINIO_ENDPOINT")
            or os.getenv("AWS_S3_ENDPOINT_URL")
            or "localhost:9000"
        )

        minio_secure = minio_endpoint_raw.startswith("https://")
        minio_endpoint = (
            minio_endpoint_raw
            .removeprefix("http://")
            .removeprefix("https://")
        )

        return Minio(
            minio_endpoint,
            access_key=os.getenv("MINIO_ACCESS_KEY") or os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
            secure=minio_secure
        )

    async def getExistingMetadata(self, media_id: UUID):
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
                SELECT ReportArtifacts AS "reportartifacts"
                FROM "Cases_DB"."Reports"
                WHERE ImageId = $1
                AND ReportArtifacts IS NOT NULL
                LIMIT 1
                """,
                media_id
            )

            if row is None:
                return None
            
            return row["reportartifacts"]
        
        finally:
            await connection.close()

    async def saveMetadata(self, media_id: UUID, metadata: dict):
        connection = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT
        )

        try:
            await connection.execute(
                """
                UPDATE "Cases_DB"."Reports"
                SET ReportArtifacts = $1::jsonb
                WHERE ImageId = $2
                AND ReportArtifacts IS NULL
                """,
                json.dumps(metadata),
                media_id
            )

        finally:
            await connection.close()

    async def analyse(self, media_id: UUID):
        metadata = await self.getExistingMetadata(media_id)

        if metadata is None:
            media_record = await self.getMediaRecord(media_id)

            with tempfile.NamedTemporaryFile(
                suffix=media_record["extension"],
                delete=True
            ) as temp_file:
                # download the MINIO object here
                await self.downloadMedia(media_record,temp_file.name)

                # extract the metadata from the downloaded file
                metadata = await self.extract(
                    file_path=temp_file.name,
                    media_record=media_record
                )
            
            await self.saveMetadata(media_id, metadata)
        
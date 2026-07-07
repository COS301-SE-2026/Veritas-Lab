from abc import ABC, abstractmethod
from uuid import UUID
import asyncpg
from dotenv import load_dotenv
from app.core.env import ENVLoader
from minio import Minio
import os
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

    @abstractmethod
    async def extract(self, file_path: str, media_record: dict):
        pass
    
    async def get_media_record(self, media_id: UUID):
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

    async def download_media(self, media_record: dict, file_path: str):
        minio_client = self.create_minio_client()

        await run_in_threadpool(
            minio_client.fget_object,
            bucket_name=media_record["bucket"],
            object_name=media_record["object_name"],
            file_path=file_path
        )
    
    def creat_minio_client(self):
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

    async def analyse(self, media_id: UUID):
        media_record = await self.get_media_record(media_id)

        with tempfile.NamedTemporaryFile(
            suffix=media_record["extension"],
            delete=True
        ) as temp_file:
            await self.download_media(media_record,temp_file.name)

            metadata = await self.extract(
                file_path=temp_file.name,
                media_record=media_record
            )
        
from abc import ABC, abstractmethod
from uuid import UUID
import asyncpg
from dotenv import load_dotenv
from app.core.env import ENVLoader
import os
import tempfile

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
        
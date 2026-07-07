import exiftool
import asyncpg
import tempfile
import os
from cases import Case
from uuid import UUID
from media_service import MediaService
from minio import Minio


# class PNGService(MediaService):

#     async def extract(self, media_id: UUID):
        
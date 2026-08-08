from abc import ABC, abstractmethod #abstractmethod is to override methods
from uuid import UUID
import asyncpg
import exiftool
from app.core.env import Minio_Settings, R2_Settings, Other_Settings, Postgres_Settings
from minio import Minio
import json
from urllib.parse import urlparse
from pathlib import Path
import aiofiles.tempfile
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel
import boto3
from botocore.client import Config
from mypy_boto3_s3 import S3Client

minio_settings = Minio_Settings()
r2_settings = R2_Settings()
other_settings = Other_Settings()
postgres_settings = Postgres_Settings()

def get_object() -> S3Client:
    if other_settings.ENVIRONMENT == "development":
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
                s3={"addressing_style": "path"}
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
                s3={"addressing_style": "path"}
            ),
        )

class AnalysisFindings(BaseModel):
    Certainty: int
    Findings: str

class MediaService(ABC):

    async def extract(self, file_path: str, media_record: dict):
        def run_exiftool():
            with exiftool.ExifToolHelper() as et:
                return et.get_metadata(file_path)

        metadata_list = await run_in_threadpool(run_exiftool)
        metadata = metadata_list[0] if metadata_list else {}
        extension = media_record["extension"].replace(".", "").upper()

        if extension == "JPG":
            extension = "JPEG"

        return {
            "media_id": str(media_record["media_id"]),
            "file_type": extension,
            "bucket": media_record["bucket"],
            "object_name": media_record["object_name"],
            "metadata": metadata
        }
    
    async def get_media_record(self, media_id: UUID):
        connection = await asyncpg.connect(
            user=postgres_settings.DB_USER,
            password=postgres_settings.DB_PASSWORD,
            database=postgres_settings.DB_NAME,
            host=postgres_settings.DB_HOST,
            port=postgres_settings.DB_PORT,
            ssl="require" if postgres_settings.DB_SSL else None,
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
        storage_client = get_object()

        def _download_from_s3() -> None:
            with open(file_path, "wb") as file_obj:
                storage_client.download_fileobj(
                    Bucket=media_record["bucket"],
                    Key=media_record["object_name"],
                    Fileobj=file_obj,
                )

        await run_in_threadpool(_download_from_s3)


    
    

    async def get_existing_metadata(self, media_id: UUID):
        connection = await asyncpg.connect(
            user=postgres_settings.DB_USER,
            password=postgres_settings.DB_PASSWORD,
            database=postgres_settings.DB_NAME,
            host=postgres_settings.DB_HOST,
            port=postgres_settings.DB_PORT,
            ssl="require" if postgres_settings.DB_SSL else None,
        )

        try:
            row = await connection.fetchrow(
                """
                SELECT ReportArtifacts AS "reportartifacts"
                FROM "Cases_DB"."Reports"
                WHERE MediaId = $1
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

    async def save_metadata(self, media_id: UUID, metadata: dict):
        connection = await asyncpg.connect(
            user=postgres_settings.DB_USER,
            password=postgres_settings.DB_PASSWORD,
            database=postgres_settings.DB_NAME,
            host=postgres_settings.DB_HOST,
            port=postgres_settings.DB_PORT,
            ssl="require" if postgres_settings.DB_SSL else None,
        )

        try:
            await connection.execute(
                """
                UPDATE "Cases_DB"."Reports"
                SET ReportArtifacts = $1::jsonb
                WHERE MediaId = $2
                AND ReportArtifacts IS NULL
                """,
                json.dumps(metadata),
                media_id
            )

        finally:
            await connection.close()

    async def update_analysis(self, media_id: UUID, analysis: AnalysisFindings) -> None:
        connection = await asyncpg.connect(
            user=postgres_settings.DB_USER,
            password=postgres_settings.DB_PASSWORD,
            database=postgres_settings.DB_NAME,
            host=postgres_settings.DB_HOST,
            port=postgres_settings.DB_PORT,
            ssl="require" if postgres_settings.DB_SSL else None,
        )

        try:
            await connection.execute(
                """
                UPDATE "Cases_DB"."Reports"
                SET
                    ReportFindings = $1,
                    ReportCertainty = $2
                WHERE MediaId = $3
                """,
                analysis.Findings,
                analysis.Certainty,
                media_id
            )
        finally:
            await connection.close()

    async def analyse(self, media_id: UUID):
        metadata = await self.get_existing_metadata(media_id)
        combined_findings = None

        if metadata is None:
            media_record = await self.get_media_record(media_id)

            async with aiofiles.tempfile.TemporaryDirectory() as temp_dir:
                file_path = Path(temp_dir) / f"{media_id}{media_record['extension']}"
                await self.download_media(media_record, str(file_path))

                metadata = await self.extract(
                    file_path=str(file_path),
                    media_record=media_record
                )

                ai_analysis = await self.ai_analysis(file_path)
                
            #This is to remove information about the system that does not 
            #affect the analysis
            if "SourceFile" in metadata:
                del metadata["SourceFile"]
            if "ExifTool:ExifToolVersion" in metadata:
                del metadata["ExifTool:ExifToolVersion"]
            if "File:Directory" in metadata:
                del metadata["File:Directory"]

            await self.save_metadata(media_id, metadata)
            
            report_findings = await self.analyse_metadata(metadata)

            final_risk_level = max(
                int(ai_analysis["risk_level"]),
                report_findings.Certainty
            )

            combined_findings = {
                **ai_analysis,
                "risk_level": final_risk_level,
                "findings": report_findings.Findings
            }
            print(json.dumps(combined_findings, indent=4))

            # use this when you want to upload to the database
            final_findings = self.create_findings_string(combined_findings)
            final_analysis = AnalysisFindings(Certainty=final_risk_level, Findings=final_findings)
            await self.update_analysis(media_id=media_id, analysis=final_analysis)

        if combined_findings is None:
           return None
        
        return combined_findings
    
    @abstractmethod
    async def analyse_metadata(self,metadata: dict)-> AnalysisFindings:
        pass

    @abstractmethod
    async def ai_analysis(self, path : str|Path) ->dict:
        pass

    @abstractmethod
    def create_findings_string(self, input: dict) ->str:
        pass
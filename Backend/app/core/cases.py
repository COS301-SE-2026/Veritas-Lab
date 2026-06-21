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

        connection = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT
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
                    # Insesrt into the Reports table allowing the report to have the image's name in the image title column

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

    def toJSON(self):
        return {
            "caseId": str(self.CaseId) if self.CaseId is not None else None,
            "caseName": self.CaseName,
            "caseCreator": self.CaseCreator,
            "caseReviews": self.CaseReviews,
            "caseDescription": self.CaseDescription,
            "caseClosed": self.CaseClosed,
            "caseCreationDate": self.CaseCreationDate.isoformat() if self.CaseCreationDate else None
        }
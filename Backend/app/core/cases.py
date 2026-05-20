import asyncpg
import json
from app.core.env import ENVLoader

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
    

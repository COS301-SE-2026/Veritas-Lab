from uuid import uuid4
from datetime import datetime, timezone
import asyncpg

class Case:
    def __init__(self, CaseCreator: str = None, CaseName: str = None, CaseReviews: dict = None):
        if not CaseCreator:
            raise ValueError("CaseCreator is required")
        if not CaseName:
            raise ValueError("CaseName is required")
        if len(CaseName) > 255:
            raise ValueError("CaseName must be 255 characters or less")
        if len(CaseCreator) > 100:
            raise ValueError("CaseCreator must be 100 characters or less")

        self.CaseId = str(uuid4())
        self.CaseCreator = CaseCreator
        self.CaseName = CaseName
        self.CaseReviews = CaseReviews
        self.CaseCreationDate = datetime.now(timezone.utc)

    async def save(self):
        connection = await asyncpg.connect(
            user="postgres",
            password="",
            database="",
            host="localhost",
            port=8001
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
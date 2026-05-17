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
        pass

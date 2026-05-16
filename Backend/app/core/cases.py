from uuid import uuid4
from datetime import datetime
import asyncpg

class Case:
    
    def __init__(self, CaseCreator: str = None, CaseName: str = None, CaseReviews: dict = None):
        pass
    
    async def save(self):
        pass

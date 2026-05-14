from fastapi import FastAPI
import re
from pydantic import BaseModel # For JSON
from app.auth.auth import router as auth_router

app = FastAPI(
    title="Veritas Lab API",
    description="This is the backend REST API for Veritas Lab"
)

app.include_router(auth_router)

@app.get("/")
def root():
    return {
        "status":"success",
        "message":"The API is running..."
    }




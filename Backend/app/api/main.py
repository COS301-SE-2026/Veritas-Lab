from fastapi import FastAPI
import re
from pydantic import BaseModel # For JSON

app = FastAPI(
    title="Veritas Lab API",
    description="This is the backend REST API for Veritas Lab"
)

@app.get("/")
def root():
    return {
        "status":"success",
        "message":"The API is running..."
    }




from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import re
import os
from pydantic import BaseModel # For JSON
from app.auth.auth import router as auth_router
from app.api.routers.cases_router import router as cases_router

app = FastAPI(
    title="Veritas Lab API",
    description="This is the backend REST API for Veritas Lab"
)


allowed_origins = [
    os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=os.environ.get(
        "FRONTEND_ORIGIN_REGEX",
        r"^https://your-app-[a-z0-9-]+-yourteam\.vercel\.app$",
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(cases_router)

app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "status":"success",
        "message":"The API is running..."
    }




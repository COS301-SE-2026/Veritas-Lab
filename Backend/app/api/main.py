from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import re
import os
from pydantic import BaseModel # For JSON
from app.auth.auth import router as auth_router
from app.api.routers.cases_router import router as cases_router
from app.core.env import ENVLoader

IS_PROD = os.environ.get("ENVIRONMENT", "development").strip().lower() == "production"

app = FastAPI(
    title="Veritas Lab API",
    description="This is the backend REST API for Veritas Lab",
    docs_url=None if IS_PROD else "/docs",
    redoc_url=None if IS_PROD else "/redoc",
    openapi_url=None if IS_PROD else "/openapi.json",
)


allowed_origins = [
    os.environ.get("FRONTEND_ORIGIN", ""),
]
if os.environ.get("ENVIRONMENT", "development") != "production": allowed_origins.append("http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=os.environ.get(
        "FRONTEND_ORIGIN_REGEX",
        r"^https://veritsalab-[a-z0-9-]+\.vercel\.app$"
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




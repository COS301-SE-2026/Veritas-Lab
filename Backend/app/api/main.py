from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.auth.auth import router as auth_router
from app.api.routers.cases_router import router as cases_router
from app.core.env import Other_Settings

other_settings = Other_Settings()

app = FastAPI(
    title="Veritas Lab API",
    description="This is the backend REST API for Veritas Lab",
    docs_url=None if other_settings.ENVIRONMENT == "production" else "/docs",
    redoc_url=None if other_settings.ENVIRONMENT == "production" else "/redoc",
    openapi_url=None if other_settings.ENVIRONMENT == "production" else "/openapi.json",
)


allowed_origins = [
    other_settings.FRONTEND_ORIGIN,
]

if (other_settings.ENVIRONMENT == "development"):
    allowed_origins.append("http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=other_settings.FRONTEND_ORIGIN_REGEX,
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




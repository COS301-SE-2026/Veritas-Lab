from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.auth import router as auth_router
from app.api.routers.cases_router import router as cases_router
from app.core.env import Postgres_Settings,Other_Settings
from app.core.media_relay import get_service
from contextlib import asynccontextmanager
import asyncpg
import torch

torch.set_num_threads(2)
torch.set_num_interop_threads(1)

other_settings = Other_Settings()
postgres_settings = Postgres_Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(
        user=postgres_settings.DB_USER,
        password=postgres_settings.DB_PASSWORD,
        database=postgres_settings.DB_NAME,
        host=postgres_settings.DB_HOST,
        port=postgres_settings.DB_PORT,
        ssl="require" if postgres_settings.DB_SSL else None,
        min_size=5,
        max_size=30
    )

    try:
        print("Loading AI services...")

        get_service("image")
        get_service("pdf")
        get_service("video")

        print("AI services loaded.")

        yield

    finally:
        await app.state.pool.close()

app = FastAPI(
    title="Veritas Lab API",
    description="This is the backend REST API for Veritas Lab",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
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




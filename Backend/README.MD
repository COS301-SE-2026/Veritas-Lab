# Folder Structure for Backend:
```
Backend/
└── app/
    ├── api/        #fastapi routers
    ├── core/       #cross cutting concerns that all modules require handled here (config.py, security.py etc...)
    ├── database/   #everything for the PostgreSQL + Redis caching
    ├── ml/         #Machine Learning
    ├── models/     #ORM model classes handled here
    ├── search/     #OpenSearch interaction
    ├── tasks/      #celery for ML jobs
    ├── tests/      #pyTest suite
    ├── storage/    #AWS S3 storage
    ├── services/   #business logic
    ├── auth/       #authorization logic here
    ├── DockerFile
    ├── README.MD
    └── .dockerignore
```

# how to install the python packages:
navigate to the backend direcotry and then run:
```
python -m pip install -r requirements/base.txt
```

# Python imports:
Installed with explanation of why and how to use:

## fastapi and Server
- fastapi             - from fastapi import FastAPI (define routes)
- uvicorn[standard]   - import uvicorn (run with uvicorn app.main:app --reload)
    [standard] - installs websocket support and faster HTTP 
- python-multipart    - from fastapi import UploadFile, File (uploaded files include images, video, audio and PDFs)
- pydantic            - from pydantic import BaseModel (define the shape of every request and respone in the api)
- pydantic-settings   - from pydantic_settings import BaseSettings (we will use this in core for the config, it will read and validate the .env vars)

## Database
- sqlalchemy[asyncio] - from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine (AsyncSession opens database connections, create_async_engine sets up the PostgreSQL connection)
    [asyncio] - unlocks async mode in SQLAlchemy without it SQLAlchemy runs synchronously and bloks our fastapi routes
- asyncpg             - SQLAlchemy uses it automatically when our connection string starts with postgresql+asyncpg://
- alembic             - keeps the real PostgreSQL tables in sync with our ORM models as they change

## Auth
- python-jose         - from jose import jwt (encodes tokens when user logs in and decodes them on every request to validate identity)
    [cryptography] - unlocks RS256 signing using public/private key pairs which is more secure 
- passlib             - from passlib.context import CryptContext (hashes passwords on registration and verifies them on login never touches JWT)
    [bcrypt] - the actual hashing algorithm

## Redis and Celery
- celery              - from celery import Celery (creates Celery instance in tasks/celery_app.py and registers all background task)
    [redis] - installs the Redis transport so Celery has a broker to send and receive tasks through (without it Celery cannot run)
- redis               - import redis (used for database/redis.py to create connection pool for caching in cache_service and job status tracking)

## Metadata
- Pillow              - from PIL import Image, ExifTags (opens image files and extracts metadata like camera info, GPS, timestamps and editing software)
- pyexiftool          - import exiftool (deeper metadata extraction across all file types including audio and video, requires ExifTool installed on the OS)
    note: you might need to run: install -y libimage-exiftool-perl (check. for your own os this might be wrong. -- will update when verified)

- python-magic        - import magic (detects the true MIME type of a file regardless of its extension so as to correctly identify file for our artifact validation)
- PyMuPDF             - import fitz (reads and renders PDF pages for our document detector and extracts text and page images to detect manipulation)

## Testing
- pytest              - import pytest (base testing framework every test file uses @pytest.mark.asyncio and @pytest.fixture decorators)
- pytest-asyncio      - import pytest_asyncio (allows test functions to be async so they can test our async fastapi routes and services without blocking)
- pytest-cov          - run as pytest --cov=app in terminal (generates a coverage report)
- httpx               - from httpx import AsyncClient (creates a test client in tests/conftest.py that sends fake HTTP requests without needing a running server)
- fakeredis           - import fakeredis (creates an in memory fake Redis so our tests never need a real Redis connection running)
- moto                - from moto import mock_s3 (intercepts all boto3 S3 calls during tests and fakes them so tests never touch real AWS buckets)
    [s3] - only installs the S3 mocking component. moto covers all AWS services so we specify only what we need to keep it lightweight

    note: the above will likely need to be updated when real tests are done

## Storage
-boto3                - import boto3 (AWS SDK that handles S3 upload and object management we use it in storage/storage_service.py)
-aioboto3             - import aioboto3 (async wrapper around boto3 necessary because the fastapi routes and Celery tasks are async so S3 calls cannot block)

## Search
- opensearch-py       - from opensearch_py import OpenSearch (covers index management, document ingest and all query types used in search/queries.py)

# Currently not installed but will do so once we require them:

## ML and Computer Vision
- torch
- torchvision
- torchaudio
- transformers
- datasets
- accelerate
- huggingface-hub
- opencv-python-headless
- numpy
- scikit-learn
- scipy

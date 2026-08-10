from pydantic_settings import BaseSettings, SettingsConfigDict

class Postgres_Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_SSL: bool
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

class Auth_Settings(BaseSettings):
    JWT_SECRET: str
    HASH: str
    TOKEN_EXPIRE: int
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

class R2_Settings(BaseSettings):
    R2_TOKEN_VALUE: str
    R2_URL: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

class User_Settings(BaseSettings):
    ADMIN_NAME: str
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    E2E_USER_NAME: str
    E2E_USER_EMAIL: str
    E2E_USER_PASSWORD: str
    E2E_INVESTIGATOR_NAME: str
    E2E_INVESTIGATOR_EMAIL: str
    E2E_INVESTIGATOR_PASSWORD: str
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

class Minio_Settings(BaseSettings):
    MINIO_EXTERNAL_URL: str
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_API_PORT: int
    MINIO_CONSOLE_PORT: int
    AWS_REGION: str
    STORAGE_URL: str
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

class Other_Settings(BaseSettings):
    ENVIRONMENT: str
    NEXT_PUBLIC_API_URL: str
    FRONTEND_ORIGIN: str
    FRONTEND_ORIGIN_REGEX: str =(
        r"^https://veritsalab-[a-z0-9-]+\.vercel\.app$"
    )
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

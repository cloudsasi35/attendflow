"""Configuration for AttendFlow backend."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # App
    app_env: str = "development"
    app_name: str = "AttendFlow"
    debug: bool = False

    # Database
    database_url: str = "postgresql+psycopg://attendflow:attendflow@localhost:5432/attendflow"

    # JWT
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_access_token_expire_minutes: int = 15
    jwt_algorithm: str = "HS256"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Timezone
    org_timezone: str = "Asia/Kolkata"

    # Seed
    seed_demo_data: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

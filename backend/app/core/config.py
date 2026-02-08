from __future__ import annotations

import logging.config
import os
from pathlib import Path

from pydantic import AnyHttpUrl, PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration class for managing application settings."""

    # Project info
    PROJECT_NAME: str = "Receipt Scanner API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Database settings
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "receipt_scanner")
    DB_ECHO_LOG: bool = False

    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    LOGFIRE_TOKEN: str = os.getenv("LOGFIRE_TOKEN", "")

    # JWT Authentication
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", "your-secret-key-change-in-production"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # File upload settings
    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE_MB: int = 10

    # CORS Settings
    ALLOWED_ORIGINS: list[AnyHttpUrl] = []

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @model_validator(mode="after")
    def set_default_origins(self) -> Settings:
        if not self.ALLOWED_ORIGINS:
            self.ALLOWED_ORIGINS = [AnyHttpUrl("http://localhost:3000")]
        return self

    @model_validator(mode="after")
    def validate_jwt_secret(self) -> Settings:
        """Validate JWT secret key is secure and not using default value."""
        if self.JWT_SECRET_KEY == "your-secret-key-change-in-production":  # noqa: S105
            raise ValueError(
                "SECURITY ERROR: JWT_SECRET_KEY must be changed from default value.\n"
                "Generate a secure key:\n"
                "  python -c 'import secrets; print(secrets.token_urlsafe(32))'\n"
                "Then set it in your .env file or environment variables."
            )
        if len(self.JWT_SECRET_KEY) < 32:
            raise ValueError(
                f"SECURITY ERROR: JWT_SECRET_KEY must be at least 32 characters long.\n"
                f"Current length: {len(self.JWT_SECRET_KEY)} characters\n"
                "Generate a secure key:\n"
                "  python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        return self

    @property
    def database_url(self) -> str:
        """Constructs database URL from config values."""
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_HOST,
                port=int(self.POSTGRES_PORT),
                path=self.POSTGRES_DB,
            )
        )

    def validate_api_keys(self) -> None:
        """Validates necessary API keys are set."""
        if not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

    @staticmethod
    def setup_logging() -> None:
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d - %(funcName)s()] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def setup_directories(self) -> None:
        """Create necessary directories."""
        self.UPLOAD_DIR.mkdir(exist_ok=True)

    @property
    def max_upload_size_bytes(self) -> int:
        """Maximum upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


# Create global settings instance
settings = Settings()

# Setup logging
settings.setup_logging()

# Create required directories
settings.setup_directories()

# Validate API keys only when needed (can be called by services that require them)
# settings.validate_api_keys()  # Commented out to allow app to start without API key

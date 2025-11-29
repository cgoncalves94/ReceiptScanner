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

    # File upload settings
    UPLOAD_DIR: Path = Path("uploads")

    # CORS Settings
    ALLOWED_ORIGINS: list[AnyHttpUrl] = []

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @model_validator(mode="after")
    def set_default_origins(self) -> "Settings":
        if not self.ALLOWED_ORIGINS:
            self.ALLOWED_ORIGINS = [AnyHttpUrl("http://localhost:3000")]
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


# Create global settings instance
settings = Settings()

# Setup logging
settings.setup_logging()

# Create required directories
settings.setup_directories()

# Validate API keys only when needed (can be called by services that require them)
# settings.validate_api_keys()  # Commented out to allow app to start without API key

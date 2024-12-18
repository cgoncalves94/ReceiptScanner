import logging.config
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import AnyHttpUrl, PostgresDsn, model_validator
from pydantic_settings import BaseSettings

# Load environment variables from .env file at module level
load_dotenv()


class Settings(BaseSettings):
    """Configuration class for managing application settings."""

    # Project info
    PROJECT_NAME: str = "Receipt Scanner API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Database settings
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "receipt_analyzer")
    DB_ECHO_LOG: bool = False

    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # File upload settings
    UPLOAD_DIR: Path = Path("uploads")
    UPLOADS_ORIGINAL_DIR: Path = UPLOAD_DIR / "original"
    UPLOADS_PROCESSED_DIR: Path = UPLOAD_DIR / "processed"

    # CORS Settings
    ALLOWED_ORIGINS: list[AnyHttpUrl] = ()

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

    @model_validator(mode="after")
    def set_default_origins(self) -> "Settings":
        if not self.ALLOWED_ORIGINS:
            self.ALLOWED_ORIGINS = [AnyHttpUrl("http://localhost:3000")]
        return self

    @classmethod
    def assemble_cors_origins(cls, v: str | list[str] | None) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v if v is not None else []

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

    def validate_api_keys(self):
        """Validates necessary API keys are set."""
        if not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

    @staticmethod
    def setup_logging():
        """Set up logging configuration."""
        logging_format = "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d - %(funcName)s() ] %(message)s"
        logging.basicConfig(
            level=logging.INFO,
            format=logging_format,
        )

    def setup_directories(self):
        """Create necessary directories."""
        self.UPLOAD_DIR.mkdir(exist_ok=True)
        self.UPLOADS_ORIGINAL_DIR.mkdir(exist_ok=True, parents=True)
        self.UPLOADS_PROCESSED_DIR.mkdir(exist_ok=True, parents=True)


# Create global settings instance
settings = Settings()

# Setup logging
settings.setup_logging()

# Create required directories
settings.setup_directories()

# Validate API keys only when needed (can be called by services that require them)
# settings.validate_api_keys()  # Commented out to allow app to start without API key

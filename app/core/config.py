import logging.config
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import PostgresDsn


class Config:
    """Configuration class for managing application settings."""

    # Load environment variables from .env file
    load_dotenv()

    # Project info
    PROJECT_NAME: str = "Receipt Scanner API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database settings
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "db")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "receipt_analyzer")

    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # File upload settings
    UPLOAD_DIR: Path = Path("uploads")
    UPLOAD_DIR.mkdir(exist_ok=True)

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

    def validate(self):
        """Validates necessary configurations are set."""
        missing_vars = []
        required_vars = ["GEMINI_API_KEY"]

        for var_name in required_vars:
            if not getattr(self, var_name):
                missing_vars.append(var_name)

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

    def __init__(self):
        # Validate configurations
        self.validate()

        # Set up logging
        logging_format = "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d - %(funcName)s() ] %(message)s"
        logging.basicConfig(
            level=logging.INFO,
            format=logging_format,
        )


settings = Config()

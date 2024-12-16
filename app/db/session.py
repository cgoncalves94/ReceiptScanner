import logging

from sqlmodel import Session, create_engine

from app.core.config import settings

logger = logging.getLogger(__name__)

# Log the database URL (remove sensitive info first)
db_url = settings.database_url
safe_db_url = db_url.replace(settings.POSTGRES_PASSWORD, "****")
logger.debug(f"Attempting to connect to database with URL: {safe_db_url}")

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Enable connection pool "pre-ping" feature
)

# Create SessionLocal class for dependency injection
SessionLocal = Session

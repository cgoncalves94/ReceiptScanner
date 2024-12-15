from sqlmodel import Session, create_engine

from app.core.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Enable connection pool "pre-ping" feature
)

# Create SessionLocal class for dependency injection
SessionLocal = Session

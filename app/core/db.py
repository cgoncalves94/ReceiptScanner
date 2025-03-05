import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.sql import text
from sqlmodel import SQLModel

from app.core.config import settings

logger = logging.getLogger(__name__)

# -------------------------------------------
# 1. Database Engine Creation
# -------------------------------------------
engine = create_async_engine(
    settings.database_url,
    echo=settings.DB_ECHO_LOG,
    future=True,
)

# Create session factory
async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)


# -------------------------------------------
# 2. Database Initialization
# -------------------------------------------
async def init_db() -> None:
    """Initialize the database."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database initialized successfully")


# -------------------------------------------
# 3. Database Health Check
# -------------------------------------------
async def check_db_connection() -> bool:
    """
    Check if the database connection is healthy.
    Returns True if connected, False otherwise.
    """
    try:
        # Try to create a connection and execute a simple query

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        return True
    except SQLAlchemyError as e:
        logger.error(f"Database health check failed: {e}")
        return False

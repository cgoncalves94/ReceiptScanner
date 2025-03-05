import logging

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
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

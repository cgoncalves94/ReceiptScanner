import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)

# -------------------------------------------
# 1. Database Engine Creation
# -------------------------------------------
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,  # Enable connection health checks
)


# -------------------------------------------
# 2. Database Initialization
# -------------------------------------------
async def init_db() -> None:
    """Initialize database by creating all tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("Database initialized successfully")
    except SQLAlchemyError:
        raise DatabaseError(
            "Database connection failed. Please ensure PostgreSQL is running on port 5432"
        ) from None


# -------------------------------------------
# 3. Database Session Factory
# -------------------------------------------
@asynccontextmanager
async def create_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session."""
    async with AsyncSession(engine) as session:
        yield session

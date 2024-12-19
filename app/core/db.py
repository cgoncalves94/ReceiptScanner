import functools
import logging
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any, TypeVar

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
# Create a single engine instance
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
        # Direct error without status code
        raise DatabaseError(
            "Database connection failed. Please ensure PostgreSQL is running on port 5432"
        ) from None


# -------------------------------------------
# 3. Database Session Management
# -------------------------------------------
@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with AsyncSession(engine) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# -------------------------------------------
# 4. Transactional Decorator
# -------------------------------------------
T = TypeVar("T")


def transactional(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle database transactions.

    Usage:
        @transactional
        async def my_service_method(self, ...):
            # Method will be wrapped in a transaction
            ...
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        if not hasattr(args[0], "session") or not isinstance(
            args[0].session, AsyncSession
        ):
            raise ValueError("Transactional decorator requires 'session' attribute")

        try:
            async with args[0].session.begin_nested():
                return await func(*args, **kwargs)
        except SQLAlchemyError:
            # Let SQLAlchemy errors propagate for consistent handling
            raise

    return wrapper

from collections.abc import AsyncGenerator

from sqlmodel.ext.asyncio.session import AsyncSession

from .db import async_session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

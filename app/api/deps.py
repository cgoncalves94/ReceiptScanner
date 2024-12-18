from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_session
from app.services import CategoryService, ReceiptService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    try:
        async for session in get_session():
            try:
                yield session
            finally:
                await session.close()
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is currently unavailable. Please try again later.",
        ) from e


# Type alias for cleaner dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_receipt_service(session: DbSession) -> ReceiptService:
    """Get a ReceiptService instance with database session."""
    return ReceiptService(session)


async def get_category_service(session: DbSession) -> CategoryService:
    """Get a CategoryService instance with database session."""
    return CategoryService(session)


# Type aliases for service dependencies
ReceiptServiceDep = Annotated[ReceiptService, Depends(get_receipt_service)]
CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]

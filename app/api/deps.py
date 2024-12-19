import logging
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import get_session
from app.services import CategoryService, ReceiptScannerService, ReceiptService

logger = logging.getLogger(__name__)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with get_session() as session:
        yield session


# Type alias for cleaner dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_receipt_service(session: DbSession) -> ReceiptService:
    """Get a ReceiptService instance with database session."""
    return ReceiptService(session)


async def get_category_service(session: DbSession) -> CategoryService:
    """Get a CategoryService instance with database session."""
    return CategoryService(session)


async def get_receipt_scanner_service() -> ReceiptScannerService:
    """Get a ReceiptScannerService instance."""
    return ReceiptScannerService()


# Type aliases for service dependencies
ReceiptServiceDep = Annotated[ReceiptService, Depends(get_receipt_service)]
CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]
ReceiptScannerDep = Annotated[
    ReceiptScannerService, Depends(get_receipt_scanner_service)
]

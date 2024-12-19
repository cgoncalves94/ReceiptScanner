import logging
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import create_session
from app.services import CategoryService, ReceiptService, ScannerService

logger = logging.getLogger(__name__)


# -------------------------------------------
# 1. Database Session Dependency
# -------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with transaction management."""
    async with create_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Type alias for cleaner dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]


# -------------------------------------------
# 2. Service Dependencies
# -------------------------------------------
async def get_receipt_service(session: DbSession) -> ReceiptService:
    """Get a ReceiptService instance with database session."""
    return ReceiptService(session)


async def get_category_service(session: DbSession) -> CategoryService:
    """Get a CategoryService instance with database session."""
    return CategoryService(session)


async def get_receipt_scanner_service(session: DbSession) -> ScannerService:
    """Get a ReceiptScannerService instance with database session."""
    return ScannerService(session)


# Type aliases for service dependencies
ReceiptServiceDep = Annotated[ReceiptService, Depends(get_receipt_service)]
CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]
ReceiptScannerDep = Annotated[ScannerService, Depends(get_receipt_scanner_service)]

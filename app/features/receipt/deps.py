from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.deps import get_session
from app.features.category.deps import get_category_service

from .repositories import ReceiptRepository
from .services import ReceiptService


async def get_receipt_repository(
    session: AsyncSession = Depends(get_session),
) -> ReceiptRepository:
    """Get an instance of the receipt repository."""
    return ReceiptRepository(session)


async def get_receipt_service(
    receipt_repo: ReceiptRepository = Depends(get_receipt_repository),
    category_service=Depends(get_category_service),
) -> ReceiptService:
    """Get an instance of the receipt service."""
    return ReceiptService(
        session=receipt_repo.session,
        receipt_repository=receipt_repo,
        category_service=category_service,
    )


ReceiptDeps = Annotated[ReceiptService, Depends(get_receipt_service)]

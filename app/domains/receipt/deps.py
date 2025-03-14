from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.deps import get_session
from app.domains.category.deps import get_category_service

from .services import ReceiptService


async def get_receipt_service(
    session: AsyncSession = Depends(get_session),
    category_service=Depends(get_category_service),
) -> ReceiptService:
    """Get an instance of the receipt service."""
    return ReceiptService(
        session=session,
        category_service=category_service,
    )


ReceiptDeps = Annotated[ReceiptService, Depends(get_receipt_service)]

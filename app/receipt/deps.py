from typing import TYPE_CHECKING, Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.category.deps import get_category_service
from app.core.deps import get_session

from .services import ReceiptService

if TYPE_CHECKING:
    from app.category.services import CategoryService


async def get_receipt_service(
    session: AsyncSession = Depends(get_session),
    category_service: "CategoryService" = Depends(get_category_service),
) -> ReceiptService:
    """Get an instance of the receipt service."""
    return ReceiptService(
        session=session,
        category_service=category_service,
    )


ReceiptDeps = Annotated[ReceiptService, Depends(get_receipt_service)]

from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.deps import get_session

from .service import ReceiptService


async def get_receipt_service(session: AsyncSession = Depends(get_session)):
    """Get an instance of the receipt service."""
    return ReceiptService(session)


# Common dependencies
ReceiptDeps = Annotated[ReceiptService, Depends(get_receipt_service)]

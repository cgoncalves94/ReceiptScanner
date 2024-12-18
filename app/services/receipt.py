import logging
from collections.abc import Sequence

from fastapi import status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import DomainException, ErrorCode
from app.models import (
    ReceiptCreate,
    ReceiptItemCreate,
    ReceiptItemRead,
    ReceiptItemsByCategory,
    ReceiptRead,
    ReceiptUpdate,
)
from app.repositories import ReceiptRepository

logger = logging.getLogger(__name__)


class ReceiptService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ReceiptRepository(db)

    # Receipt Operations
    async def create(self, receipt_in: ReceiptCreate) -> ReceiptRead:
        """Create a new receipt."""
        receipt_dict = await self.repository.create(receipt_in=receipt_in)
        return ReceiptRead.model_validate(receipt_dict)

    async def get(self, receipt_id: int) -> ReceiptRead:
        """Get a receipt by ID with its items."""
        receipt = await self.repository.get(receipt_id=receipt_id)
        if not receipt:
            raise DomainException(
                code=ErrorCode.NOT_FOUND,
                message=f"Receipt with ID {receipt_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Get items for this receipt
        items = await self.repository.list_receipt_items(receipt_id=receipt_id)
        receipt.items = [ReceiptItemRead.model_validate(item) for item in items]
        return receipt

    async def list(self, skip: int = 0, limit: int = 100) -> Sequence[ReceiptRead]:
        """List all receipts with their items and categories."""
        return await self.repository.list(skip=skip, limit=limit)

    async def update(self, receipt_id: int, receipt_in: ReceiptUpdate) -> ReceiptRead:
        """Update a receipt."""
        db_obj = await self.repository.get(receipt_id=receipt_id)
        if not db_obj:
            raise DomainException(
                code=ErrorCode.NOT_FOUND,
                message=f"Receipt with ID {receipt_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        updated_obj = await self.repository.update(
            receipt_id=receipt_id, receipt_in=receipt_in
        )
        if not updated_obj:
            raise DomainException(
                code=ErrorCode.NOT_FOUND,
                message=f"Receipt with ID {receipt_id} not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return ReceiptRead.model_validate(updated_obj)

    async def delete(self, receipt_id: int) -> None:
        """Delete a receipt."""
        await self.get(receipt_id)
        await self.repository.delete(receipt_id=receipt_id)

    # Receipt Item Operations
    async def create_items(
        self, items_in: Sequence[ReceiptItemCreate]
    ) -> Sequence[ReceiptItemRead]:
        """Create receipt items."""
        items_dict = await self.repository.create_items(items_in=items_in)
        return [ReceiptItemRead.model_validate(item) for item in items_dict]

    async def list_items_by_category(
        self, *, category_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[ReceiptItemsByCategory]:
        """List all items in a category with aggregated values."""
        return await self.repository.list_items_by_category(
            category_id=category_id,
            skip=skip,
            limit=limit,
        )

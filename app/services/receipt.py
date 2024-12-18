import logging
from collections.abc import Sequence

from sqlmodel.ext.asyncio.session import AsyncSession

from app.exceptions import DomainException, ErrorCode
from app.repositories import ReceiptRepository
from app.schemas import (
    ReceiptCreate,
    ReceiptItemCreate,
    ReceiptItemRead,
    ReceiptItemsByCategory,
    ReceiptRead,
    ReceiptUpdate,
)

logger = logging.getLogger(__name__)


class ReceiptService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ReceiptRepository(db)

    async def create(self, receipt_in: ReceiptCreate) -> ReceiptRead:
        """Create a new receipt."""
        receipt_dict = await self.repository.create(receipt_in=receipt_in)
        return ReceiptRead.model_validate(receipt_dict)

    async def create_items(
        self, items_in: list[ReceiptItemCreate]
    ) -> list[ReceiptItemRead]:
        """Create receipt items."""
        items_dict = await self.repository.create_items(items_in=items_in)
        return [ReceiptItemRead.model_validate(item) for item in items_dict]

    async def get(self, receipt_id: int) -> ReceiptRead:
        """Get a receipt by ID (without items)."""
        receipt_dict = await self.repository.get(receipt_id=receipt_id)
        if not receipt_dict:
            raise DomainException(
                ErrorCode.NOT_FOUND, f"Receipt with ID {receipt_id} not found"
            )
        return ReceiptRead.model_validate(receipt_dict)

    async def get_with_items(self, receipt_id: int) -> ReceiptRead:
        """Get a receipt by ID with items and categories."""
        receipt_dict = await self.repository.get_with_items(receipt_id=receipt_id)
        if not receipt_dict:
            raise DomainException(
                ErrorCode.NOT_FOUND, f"Receipt with ID {receipt_id} not found"
            )
        return ReceiptRead.model_validate(receipt_dict)

    async def get_items_by_category(
        self, *, category_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[ReceiptItemsByCategory]:
        """Get all items in a category with aggregated values."""
        return await self.repository.get_items_by_category(
            category_id=category_id,
            skip=skip,
            limit=limit,
        )

    async def list(self, skip: int = 0, limit: int = 100) -> Sequence[ReceiptRead]:
        """List all receipts."""
        receipts = await self.repository.list(skip=skip, limit=limit)
        return [ReceiptRead.model_validate(receipt) for receipt in receipts]

    async def list_with_items(
        self, skip: int = 0, limit: int = 100
    ) -> Sequence[ReceiptRead]:
        """List all receipts with their items and categories."""
        receipts = await self.repository.list_with_items(skip=skip, limit=limit)
        return [ReceiptRead.model_validate(receipt) for receipt in receipts]

    async def update(self, receipt_id: int, receipt_in: ReceiptUpdate) -> ReceiptRead:
        """Update a receipt."""
        db_obj = await self.repository.get(receipt_id=receipt_id)
        if not db_obj:
            raise DomainException(
                ErrorCode.NOT_FOUND, f"Receipt with ID {receipt_id} not found"
            )
        updated_obj = await self.repository.update(
            receipt_id=receipt_id, receipt_in=receipt_in
        )
        if not updated_obj:
            raise DomainException(
                ErrorCode.NOT_FOUND, f"Receipt with ID {receipt_id} not found"
            )
        return ReceiptRead.model_validate(updated_obj)

    async def delete(self, receipt_id: int) -> None:
        """Delete a receipt."""
        await self.get(receipt_id)
        await self.repository.delete(receipt_id=receipt_id)

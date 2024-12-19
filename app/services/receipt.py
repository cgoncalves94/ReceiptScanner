import logging
from collections.abc import Sequence

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import transactional
from app.core.exceptions import ResourceNotFoundError
from app.models import (
    Receipt,
    ReceiptCreate,
    ReceiptItem,
    ReceiptItemCreate,
    ReceiptItemRead,
    ReceiptItemsByCategory,
    ReceiptRead,
    ReceiptUpdate,
)
from app.repositories import ReceiptRepository

logger = logging.getLogger(__name__)


class ReceiptService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ReceiptRepository(session)

    @transactional
    async def create(self, receipt_in: ReceiptCreate) -> ReceiptRead:
        """Create a new receipt."""
        # Convert input model to DB model
        db_obj = Receipt(**receipt_in.model_dump())

        # Create through repository
        created = await self.repository.create(obj_in=db_obj)

        # Initialize with empty items list since it's a new receipt
        return ReceiptRead(**created.model_dump(), items=[])

    async def get(self, receipt_id: int) -> ReceiptRead:
        """Get a receipt by ID with its items."""
        # Get receipt with items in a single query
        db_obj = await self.repository.get_with_items(receipt_id=receipt_id)
        if not db_obj:
            raise ResourceNotFoundError("Receipt", receipt_id)

        # Convert to read models
        return ReceiptRead(
            **db_obj.model_dump(exclude={"items"}),
            items=[
                ReceiptItemRead.model_validate(item) for item in (db_obj.items or [])
            ],
        )

    async def list(self, skip: int = 0, limit: int = 100) -> Sequence[ReceiptRead]:
        """List all receipts with their items and categories."""
        receipts = await self.repository.list(skip=skip, limit=limit)
        return [
            ReceiptRead(
                **receipt.model_dump(exclude={"items"}),
                items=[
                    ReceiptItemRead.model_validate(item)
                    for item in (receipt.items or [])
                ],
            )
            for receipt in receipts
        ]

    @transactional
    async def update(self, receipt_id: int, receipt_in: ReceiptUpdate) -> ReceiptRead:
        """Update a receipt."""
        # Get existing receipt
        db_obj = await self.repository.get_with_items(receipt_id=receipt_id)
        if not db_obj:
            raise ResourceNotFoundError("Receipt", receipt_id)

        # Update through repository
        updated = await self.repository.update(
            db_obj=db_obj, obj_in=receipt_in.model_dump(exclude_unset=True)
        )

        return ReceiptRead(
            **updated.model_dump(exclude={"items"}),
            items=[
                ReceiptItemRead.model_validate(item) for item in (updated.items or [])
            ],
        )

    @transactional
    async def delete(self, receipt_id: int) -> None:
        """Delete a receipt."""
        was_deleted = await self.repository.delete(receipt_id=receipt_id)
        if not was_deleted:
            raise ResourceNotFoundError("Receipt", receipt_id)

    # Receipt Item Operations
    @transactional
    async def create_items(
        self, items_in: Sequence[ReceiptItemCreate]
    ) -> Sequence[ReceiptItemRead]:
        """Create receipt items."""
        # Convert input models to DB models
        db_items = [ReceiptItem(**item.model_dump()) for item in items_in]

        # Create through repository
        created_items = await self.repository.create_items(items_in=db_items)

        # Convert to read models
        return [ReceiptItemRead.model_validate(item) for item in created_items]

    async def list_items_by_category(
        self, *, category_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[ReceiptItemsByCategory]:
        """List all items in a category with aggregated values."""
        items = await self.repository.list_items_by_category(
            category_id=category_id,
            skip=skip,
            limit=limit,
        )
        return ReceiptItemsByCategory.from_items(list(items), category_id=category_id)

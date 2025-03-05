from collections.abc import Sequence
from datetime import UTC, datetime

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .models import (
    Receipt,
    ReceiptItem,
)


class ReceiptRepository:
    """Repository for Receipt database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, receipt: Receipt) -> Receipt:
        """Create a new receipt."""
        self.session.add(receipt)
        await self.session.flush()
        return receipt

    async def get(self, receipt_id: int) -> Receipt | None:
        """Get a receipt by ID."""
        stmt = select(Receipt).where(Receipt.id == receipt_id)
        receipt = await self.session.scalar(stmt)

        if receipt:
            # Ensure items are loaded
            await self.session.refresh(receipt, ["items"])

        return receipt

    async def list(self, *, skip: int = 0, limit: int = 100) -> Sequence[Receipt]:
        """List all receipts with pagination."""
        stmt = select(Receipt).offset(skip).limit(limit)
        results = await self.session.scalars(stmt)
        receipts = results.all()

        # Ensure items are loaded for each receipt
        for receipt in receipts:
            await self.session.refresh(receipt, ["items"])

        return receipts

    async def update(self, receipt: Receipt, update_data: dict) -> Receipt:
        """Update a receipt."""
        receipt.sqlmodel_update(update_data)
        receipt.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(receipt, ["items"])
        return receipt

    async def delete(self, receipt: Receipt) -> None:
        """Delete a receipt."""
        await self.session.delete(receipt)
        await self.session.flush()

    async def list_items_by_category(
        self, category_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[ReceiptItem]:
        """List receipt items by category."""
        stmt = (
            select(ReceiptItem)
            .where(ReceiptItem.category_id == category_id)
            .offset(skip)
            .limit(limit)
        )
        results = await self.session.scalars(stmt)
        return results.all()

    async def create_items(self, items: Sequence[ReceiptItem]) -> Sequence[ReceiptItem]:
        """Create multiple receipt items."""
        for item in items:
            self.session.add(item)
        await self.session.flush()
        return items

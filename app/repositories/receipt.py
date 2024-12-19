import builtins
import logging
from collections.abc import Sequence
from typing import Any

from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Receipt, ReceiptItem

logger = logging.getLogger(__name__)


class ReceiptRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, *, obj_in: Receipt) -> Receipt:
        """Create a new receipt using the DB model."""
        self.session.add(obj_in)
        await self.session.flush()
        await self.session.refresh(obj_in)
        return obj_in

    async def get(self, *, receipt_id: int) -> Receipt | None:
        """Get a receipt by ID."""
        return await self.session.get(Receipt, receipt_id)

    async def get_with_items(self, *, receipt_id: int) -> Receipt | None:
        """Get a receipt by ID with its items and their categories."""
        statement = (
            select(Receipt)
            .where(Receipt.id == receipt_id)
            .options(selectinload(Receipt.items).selectinload(ReceiptItem.category))
        )
        result = await self.session.exec(statement)
        return result.first()

    async def list(self, *, skip: int = 0, limit: int = 100) -> Sequence[Receipt]:
        """List receipts with their items and categories."""
        statement = (
            select(Receipt)
            .options(selectinload(Receipt.items).selectinload(ReceiptItem.category))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def update(self, *, db_obj: Receipt, obj_in: dict[str, Any]) -> Receipt:
        """Update a receipt using existing DB object and update data."""
        for field, value in obj_in.items():
            setattr(db_obj, field, value)

        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, *, receipt_id: int) -> bool:
        """Delete a receipt. Returns True if deleted, False if not found."""
        db_obj = await self.get(receipt_id=receipt_id)
        if not db_obj:
            return False
        await self.session.delete(db_obj)
        return True

    # Receipt Item Operations
    async def create_items(
        self, *, items_in: builtins.list[ReceiptItem]
    ) -> Sequence[ReceiptItem]:
        """Create multiple receipt items using DB models."""
        self.session.add_all(items_in)
        await self.session.flush()

        # Fetch items with their categories
        if items_in:
            statement = (
                select(ReceiptItem)
                .where(ReceiptItem.receipt_id == items_in[0].receipt_id)
                .options(selectinload(ReceiptItem.category))
            )
            result = await self.session.exec(statement)
            return result.all()
        return []

    async def list_receipt_items(
        self, *, receipt_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[ReceiptItem]:
        """List all items in a receipt with pagination."""
        statement = (
            select(ReceiptItem)
            .where(ReceiptItem.receipt_id == receipt_id)
            .options(selectinload(ReceiptItem.category))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def list_items_by_category(
        self, *, category_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[ReceiptItem]:
        """List all items in a category with pagination."""
        statement = (
            select(ReceiptItem)
            .where(ReceiptItem.category_id == category_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.exec(statement)
        return result.all()

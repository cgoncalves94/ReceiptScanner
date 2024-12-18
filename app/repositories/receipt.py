import logging
from collections.abc import Sequence

from sqlalchemy import func
from sqlalchemy import select as sa_select
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

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

logger = logging.getLogger(__name__)


class ReceiptRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # Receipt Operations
    async def create(self, *, receipt_in: ReceiptCreate) -> ReceiptRead:
        """Create a new receipt."""
        db_obj = Receipt.model_validate(receipt_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)

        receipt = ReceiptRead(**db_obj.model_dump(), items=[])
        await self.db.commit()
        return receipt

    async def get(self, *, receipt_id: int) -> ReceiptRead | None:
        """Get a receipt by ID."""
        statement = select(Receipt).filter_by(id=receipt_id)
        result = await self.db.exec(statement)
        db_obj = result.first()
        if not db_obj:
            return None
        return ReceiptRead(**db_obj.model_dump(), items=[])

    async def list(self, *, skip: int = 0, limit: int = 100) -> Sequence[ReceiptRead]:
        """List receipts with their items and categories."""
        statement = (
            select(Receipt)
            .options(
                selectinload(Receipt.items.prop).selectinload(ReceiptItem.category.prop)
            )
            .offset(skip)
            .limit(limit)
        )
        results = await self.db.exec(statement)
        receipts = results.all()

        return [
            ReceiptRead(
                **receipt.model_dump(),
                items=[ReceiptItemRead.model_validate(item) for item in receipt.items],
            )
            for receipt in receipts
        ]

    async def update(
        self, *, receipt_id: int, receipt_in: ReceiptUpdate
    ) -> ReceiptRead:
        """Update a receipt."""
        statement = select(Receipt).filter_by(id=receipt_id)
        result = await self.db.exec(statement)
        model_obj = result.first()

        receipt_data = receipt_in.model_dump(exclude_unset=True)
        for key, value in receipt_data.items():
            setattr(model_obj, key, value)

        self.db.add(model_obj)
        await self.db.flush()
        await self.db.refresh(model_obj)

        receipt = ReceiptRead(**model_obj.model_dump(), items=[])
        await self.db.commit()
        return receipt

    async def delete(self, *, receipt_id: int) -> None:
        """Delete a receipt."""
        statement = select(Receipt).filter_by(id=receipt_id)
        result = await self.db.exec(statement)
        model_obj = result.first()
        if model_obj:
            await self.db.delete(model_obj)
            await self.db.commit()

    # Receipt Item Operations
    async def create_items(
        self, *, items_in: Sequence[ReceiptItemCreate]
    ) -> Sequence[ReceiptItemRead]:
        """Create multiple receipt items."""
        db_objs = [ReceiptItem.model_validate(item) for item in items_in]
        self.db.add_all(db_objs)
        await self.db.flush()

        for obj in db_objs:
            await self.db.refresh(obj)

        statement = (
            select(ReceiptItem)
            .filter_by(receipt_id=db_objs[0].receipt_id)
            .options(selectinload(ReceiptItem.category))
        )
        result = await self.db.exec(statement)
        items = result.all()

        items_read = [ReceiptItemRead.model_validate(item) for item in items]
        await self.db.commit()
        return items_read

    async def list_receipt_items(
        self, *, receipt_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[ReceiptItem]:
        """List all items in a receipt with pagination."""
        statement = (
            select(ReceiptItem)
            .filter_by(receipt_id=receipt_id)
            .options(selectinload(ReceiptItem.category))
            .offset(skip)
            .limit(limit)
        )
        results = await self.db.exec(statement)
        return results.all()

    async def list_items_by_category(
        self, *, category_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[ReceiptItemsByCategory]:
        """List all items in a category with pagination, grouped by name."""
        subquery = (
            sa_select(
                ReceiptItem.name,
                func.min(ReceiptItem.id).label("id"),
                func.sum(ReceiptItem.quantity).label("quantity"),
                func.sum(ReceiptItem.price * ReceiptItem.quantity).label("total_price"),
                func.min(ReceiptItem.currency).label("currency"),
            )
            .filter_by(category_id=category_id)
            .group_by(ReceiptItem.name)
            .offset(skip)
            .limit(limit)
        )

        results = await self.db.exec(subquery)
        items = results.all()

        return [
            ReceiptItemsByCategory.from_aggregation(item, category_id=category_id)
            for item in items
        ]

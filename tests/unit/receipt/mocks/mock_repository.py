"""Mock repository for receipt unit tests."""

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from app.domains.receipt.models import Receipt, ReceiptItem
from app.domains.receipt.repositories import ReceiptRepository


class MockReceiptRepository(ReceiptRepository):
    """Mock implementation of ReceiptRepository for unit tests."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with in-memory stores."""
        super().__init__(session)
        self._receipts: dict[int, Receipt] = {}
        self._items: dict[int, list[ReceiptItem]] = {}
        self._next_receipt_id = 1
        self._next_item_id = 1

    async def create(self, receipt: Receipt) -> Receipt:
        """Create a receipt in memory."""
        # Set ID and timestamps
        receipt.id = self._next_receipt_id
        receipt.created_at = datetime.now(UTC)
        receipt.updated_at = datetime.now(UTC)

        # Store receipt
        self._receipts[receipt.id] = receipt
        self._items[receipt.id] = []
        self._next_receipt_id += 1

        return receipt

    async def get(self, receipt_id: int) -> Receipt | None:
        """Get receipt by ID from memory."""
        receipt = self._receipts.get(receipt_id)
        if receipt:
            receipt.items = self._items.get(receipt_id, [])
        return receipt

    async def list(self, *, skip: int = 0, limit: int = 100) -> Sequence[Receipt]:
        """List receipts from memory."""
        receipts = list(self._receipts.values())
        for receipt in receipts:
            receipt.items = self._items.get(receipt.id, [])
        return receipts[skip : skip + limit]

    async def update(self, receipt: Receipt, update_data: dict) -> Receipt:
        """Update receipt in memory."""
        receipt.sqlmodel_update(update_data)
        receipt.updated_at = datetime.now(UTC)
        self._receipts[receipt.id] = receipt
        return receipt

    async def delete(self, receipt: Receipt) -> None:
        """Delete receipt from memory."""
        if receipt.id in self._receipts:
            del self._receipts[receipt.id]
            del self._items[receipt.id]

    async def list_items_by_category(
        self, category_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[ReceiptItem]:
        """List receipt items by category from memory."""
        all_items = []
        for items in self._items.values():
            all_items.extend(
                [item for item in items if item.category_id == category_id]
            )
        return all_items[skip : skip + limit]

    async def create_items(self, items: Sequence[ReceiptItem]) -> Sequence[ReceiptItem]:
        """Create multiple receipt items in memory."""
        for item in items:
            if not item.receipt_id or item.receipt_id not in self._receipts:
                raise ValueError("Receipt ID required and must exist")

            item.id = self._next_item_id
            self._next_item_id += 1
            self._items[item.receipt_id].append(item)

        return items

import logging
from collections.abc import Sequence

from fastapi import HTTPException
from sqlmodel import Session

from app.models import Receipt, ReceiptItem
from app.repositories import ReceiptRepository
from app.schemas import ReceiptCreate
from app.services import CategoryService

logger = logging.getLogger(__name__)


class ReceiptService:
    def __init__(self, db: Session):
        self.db = db
        self.receipt_repo = ReceiptRepository(db)
        self.category_service = CategoryService(db)

    def create_receipt_with_items(
        self, receipt_in: ReceiptCreate, items_data: list[dict]
    ) -> Receipt:
        """Create a receipt with its items and categories."""
        try:
            # Create the receipt first
            receipt = self.receipt_repo.create(receipt_in=receipt_in)

            # Process categories and create items
            category_map = self.category_service.get_or_create_categories(items_data)
            receipt_items = []

            for item_data in items_data:
                category = category_map[item_data["category_name"]]
                receipt_item = ReceiptItem(
                    receipt_id=receipt.id,
                    name=item_data["name"],
                    price=item_data["price"],
                    quantity=item_data.get("quantity", 1.0),
                    category_id=category.id,
                )
                receipt_items.append(receipt_item)

            # Create all items in a single transaction
            self.receipt_repo.create_many_items(items=receipt_items)

            # Return the complete receipt with items
            return self.get_receipt(receipt.id)

        except Exception as e:
            logger.error(f"Error creating receipt with items: {str(e)}")
            self.receipt_repo.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error creating receipt with items: {str(e)}",
            )

    def get_receipt(self, receipt_id: int) -> Receipt:
        """Get a specific receipt by ID."""
        receipt = self.receipt_repo.get_with_items(receipt_id=receipt_id)
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        return receipt

    def list_receipts(self, skip: int = 0, limit: int = 100) -> Sequence[Receipt]:
        """List all receipts with pagination (no items loaded)."""
        return self.receipt_repo.list(skip=skip, limit=limit)

    def list_receipts_with_items(
        self, skip: int = 0, limit: int = 100
    ) -> Sequence[Receipt]:
        """List all receipts with their items."""
        return self.receipt_repo.list_with_items(skip=skip, limit=limit)

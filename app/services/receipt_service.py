import logging

from fastapi import HTTPException
from sqlmodel import Session

from app.models.receipt import Category, Receipt, ReceiptItem
from app.repositories.category_repository import CategoryRepository
from app.repositories.receipt_repository import ReceiptRepository

logger = logging.getLogger(__name__)


class ReceiptService:
    def __init__(self, db: Session):
        self.receipt_repo = ReceiptRepository(db)
        self.category_repo = CategoryRepository(db)

    def create_receipt_with_items(
        self, receipt: Receipt, items_data: list[dict]
    ) -> Receipt:
        """Create receipt with its items and categories."""
        try:
            # Create receipt
            db_receipt = Receipt.model_validate(receipt)
            db_receipt.processed = True  # Mark as processed since we have the items
            db_receipt = self.receipt_repo.create(db_receipt)

            # Get or create categories
            category_map = self._get_or_create_categories(items_data)

            # Create items with proper category IDs
            receipt_items = [
                ReceiptItem(
                    receipt_id=db_receipt.id,
                    name=item_data["name"],
                    price=item_data["price"],
                    quantity=item_data["quantity"],
                    category_id=category_map[item_data["category_name"]].id,
                )
                for item_data in items_data
            ]
            self.receipt_repo.create_items(receipt_items)

            return db_receipt

        except Exception as e:
            self.receipt_repo.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    def _get_or_create_categories(self, items_data: list[dict]) -> dict[str, Category]:
        """Get existing categories or create new ones using AI-generated descriptions."""
        category_map = {}

        # First, get all unique category names from items
        unique_categories = {
            item["category_name"]: item["category_description"] for item in items_data
        }

        # Then check which categories already exist
        for category_name, description in unique_categories.items():
            db_category = self.category_repo.get_by_name(category_name)
            if db_category:
                logger.info(f"Using existing category: {category_name}")
                category_map[category_name] = db_category
            else:
                logger.info(
                    f"Creating new category: {category_name} with description: {description}"
                )
                db_category = self.category_repo.create(
                    Category(
                        name=category_name,
                        description=description,
                    )
                )
                category_map[category_name] = db_category

        return category_map

    def list_receipts(self, skip: int = 0, limit: int = 100) -> list[Receipt]:
        """List all receipts with pagination (no items loaded)."""
        return self.receipt_repo.list(skip, limit)

    def list_receipts_with_items(
        self, skip: int = 0, limit: int = 100
    ) -> list[Receipt]:
        """List all receipts with their items."""
        return self.receipt_repo.list_with_items(skip, limit)

    def get_receipt(self, receipt_id: int) -> Receipt:
        """Get a specific receipt by ID."""
        receipt = self.receipt_repo.get_by_id(receipt_id)
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        return receipt

    def list_categories(self) -> list[Category]:
        """List all available categories."""
        return self.category_repo.list()

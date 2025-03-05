import os
import uuid
from collections.abc import Sequence
from decimal import Decimal

from fastapi import UploadFile
from PIL import Image
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.decorators import transactional
from app.core.exceptions import NotFoundError, ServiceUnavailableError
from app.features.category.models import CategoryCreate
from app.features.category.services import CategoryService
from app.integrations.pydantic_ai.receipt_agent import analyze_receipt

from .models import (
    Receipt,
    ReceiptCreate,
    ReceiptItem,
    ReceiptItemCreate,
    ReceiptUpdate,
)
from .repositories import ReceiptRepository


class ReceiptService:
    """Service for managing receipts and receipt items."""

    def __init__(
        self,
        session: AsyncSession,
        receipt_repository: ReceiptRepository,
        category_service: CategoryService,
    ) -> None:
        self.session = session
        self.repository = receipt_repository
        self.category_service = category_service

    async def create(self, receipt_in: ReceiptCreate) -> Receipt:
        """Create a new receipt."""
        receipt = Receipt(**receipt_in.model_dump())
        return await self.repository.create(receipt)

    @transactional
    async def create_from_scan(self, image_file: UploadFile) -> Receipt:
        """Create a receipt from an uploaded image file.

        This method:
        1. Saves the uploaded image
        2. Processes the image with AI to extract receipt data
        3. Creates categories if they don't exist
        4. Creates the receipt and its items

        Args:
            image_file: The uploaded receipt image

        Returns:
            The created receipt with all its items
        """
        # Generate unique filename for the image
        file_ext = os.path.splitext(image_file.filename or "receipt.jpg")[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        image_path = settings.UPLOAD_DIR / unique_filename

        # Save the uploaded file
        with open(image_path, "wb") as f:
            content = await image_file.read()
            f.write(content)

        # Open the image with PIL for processing
        pil_image = Image.open(image_path)

        # Get existing categories to help the AI model
        categories = await self.category_service.list()
        category_dicts = [
            {"name": cat.name, "description": cat.description or ""}
            for cat in categories
        ]

        try:
            # Analyze the receipt with AI
            receipt_data = await analyze_receipt(pil_image, category_dicts)

            # Create receipt record
            receipt_create = ReceiptCreate(
                store_name=receipt_data.store_name,
                total_amount=Decimal(str(receipt_data.total_amount)),
                currency=receipt_data.currency,
                purchase_date=receipt_data.date,
                image_path=str(image_path),
            )

            receipt = await self.create(receipt_create)

            # Process each item
            receipt_items: list[ReceiptItem] = []
            for item_data in receipt_data.items:
                # Get or create category
                category = await self.category_service.get_by_name(
                    item_data.category.name
                )
                if not category:
                    category_create = CategoryCreate(
                        name=item_data.category.name,
                        description=item_data.category.description,
                    )
                    category = await self.category_service.create(category_create)

                # Calculate quantity and prices
                quantity = (
                    int(item_data.quantity) if item_data.quantity.is_integer() else 1
                )

                # Round to 2 decimal places to avoid floating point precision issues
                unit_price = round(item_data.price / item_data.quantity, 2)
                total_price = round(item_data.price, 2)

                # Create receipt item
                receipt_item = ReceiptItem(
                    name=item_data.name,
                    quantity=quantity,
                    unit_price=Decimal(str(unit_price)),
                    total_price=Decimal(str(total_price)),
                    currency=item_data.currency,
                    category_id=category.id,
                    receipt_id=receipt.id,
                )
                receipt_items.append(receipt_item)

            # Add items to database
            await self.repository.create_items(receipt_items)

            # Get the updated receipt with items
            return await self.get(receipt.id)

        except Exception as e:
            # Error will be caught by the transactional decorator
            raise ServiceUnavailableError(f"Failed to analyze receipt: {str(e)}")

    async def get(self, receipt_id: int) -> Receipt:
        """Get a receipt by ID."""
        receipt = await self.repository.get(receipt_id)
        if not receipt:
            raise NotFoundError(f"Receipt with id {receipt_id} not found")
        return receipt

    async def list(self, *, skip: int = 0, limit: int = 100) -> Sequence[Receipt]:
        """List all receipts with pagination."""
        return await self.repository.list(skip=skip, limit=limit)

    async def update(self, receipt_id: int, receipt_in: ReceiptUpdate) -> Receipt:
        """Update a receipt."""
        # Get the receipt from the database
        receipt = await self.get(receipt_id)

        # Prepare update data
        update_data = receipt_in.model_dump(exclude_unset=True, exclude={"id"})

        # Pass to repository for update
        return await self.repository.update(receipt, update_data)

    async def delete(self, receipt_id: int) -> None:
        """Delete a receipt."""
        receipt = await self.get(receipt_id)
        await self.repository.delete(receipt)

    # Receipt Item Operations
    async def create_items(
        self, receipt_id: int, items_in: Sequence[ReceiptItemCreate]
    ) -> Sequence[ReceiptItem]:
        """Create multiple receipt items."""
        # Get the receipt from the database
        receipt = await self.get(receipt_id)

        items = [ReceiptItem(**item.model_dump()) for item in items_in]
        for item in items:
            item.receipt_id = receipt.id

        return await self.repository.create_items(items)

    async def list_items_by_category(
        self, category_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[ReceiptItem]:
        """List receipt items by category."""
        # Get the category directly from the database
        category = await self.category_service.get(category_id)
        if not category:
            raise NotFoundError(f"Category with id {category_id} not found")

        return await self.repository.list_items_by_category(
            category_id=category_id, skip=skip, limit=limit
        )

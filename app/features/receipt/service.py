import os
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import UploadFile
from PIL import Image
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.decorators import transactional
from app.core.exceptions import NotFoundError, ServiceUnavailableError
from app.features.category.models import CategoryCreate
from app.features.category.service import CategoryService
from app.features.receipt.models import Receipt, ReceiptRead
from app.integrations.pydantic_ai.receipt_agent import analyze_receipt

from .models import (
    ReceiptCreate,
    ReceiptItem,
    ReceiptItemCreate,
    ReceiptUpdate,
)


class ReceiptService:
    """Service for managing receipts and receipt items."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.category_service = CategoryService(session)

    async def create(self, receipt_in: ReceiptCreate) -> Receipt:
        """Create a new receipt."""
        receipt = Receipt(**receipt_in.model_dump())
        self.session.add(receipt)
        await self.session.flush()
        return receipt

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
        image_path = settings.UPLOADS_ORIGINAL_DIR / unique_filename

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
                item_create = ReceiptItemCreate(
                    name=item_data.name,
                    quantity=quantity,
                    unit_price=Decimal(str(unit_price)),
                    total_price=Decimal(str(total_price)),
                    currency=item_data.currency,
                    category_id=category.id,
                    receipt_id=receipt.id,
                )

                # Add item to database
                receipt_item = ReceiptItem(**item_create.model_dump())
                self.session.add(receipt_item)

            await self.session.flush()

            # Explicitly refresh the receipt to load all relationships
            await self.session.refresh(receipt, ["items"])

            return receipt

        except Exception as e:
            # Error will be caught by the transactional decorator
            raise ServiceUnavailableError(f"Failed to analyze receipt: {str(e)}")

    async def get(self, receipt_id: int) -> ReceiptRead:
        """Get a receipt by ID."""
        receipt = await self.session.get(Receipt, receipt_id)
        if not receipt:
            raise NotFoundError(f"Receipt with id {receipt_id} not found")

        # Ensure items are loaded
        await self.session.refresh(receipt, ["items"])

        return ReceiptRead.model_validate(receipt)

    async def list(self, *, skip: int = 0, limit: int = 100) -> Sequence[Receipt]:
        """List all receipts with pagination."""

        # Get paginated results
        stmt = select(Receipt).offset(skip).limit(limit)
        results = await self.session.scalars(stmt)
        receipts = results.all()

        # Ensure items are loaded for each receipt
        for receipt in receipts:
            await self.session.refresh(receipt, ["items"])

        return receipts

    async def update(self, receipt_id: int, receipt_in: ReceiptUpdate) -> ReceiptRead:
        """Update a receipt."""
        # Get the receipt directly from the database
        receipt = await self.session.get(Receipt, receipt_id)
        if not receipt:
            raise NotFoundError(f"Receipt with id {receipt_id} not found")

        # Update fields using sqlmodel_update
        update_data = receipt_in.model_dump(exclude_unset=True, exclude={"id"})
        receipt.sqlmodel_update(update_data)  # type: ignore

        receipt.updated_at = datetime.now(UTC)
        await self.session.flush()

        # Ensure items are loaded
        await self.session.refresh(receipt, ["items"])

        return ReceiptRead.model_validate(receipt)

    async def delete(self, receipt_id: int) -> None:
        """Delete a receipt."""
        # Get the receipt directly from the database
        receipt = await self.session.get(Receipt, receipt_id)
        if not receipt:
            raise NotFoundError(f"Receipt with id {receipt_id} not found")

        await self.session.delete(receipt)

    # Receipt Item Operations
    async def create_items(
        self, receipt_id: int, items_in: Sequence[ReceiptItemCreate]
    ) -> Sequence[ReceiptItem]:
        """Create multiple receipt items."""
        # Get the receipt directly from the database
        receipt = await self.session.get(Receipt, receipt_id)
        if not receipt:
            raise NotFoundError(f"Receipt with id {receipt_id} not found")

        items = [ReceiptItem(**item.model_dump()) for item in items_in]
        for item in items:
            item.receipt_id = receipt.id
            self.session.add(item)

        await self.session.flush()
        return items

    async def list_items_by_category(
        self, category_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[ReceiptItem]:
        """List receipt items by category."""
        # Get the category directly from the database
        category = await self.category_service.get(category_id)
        if not category:
            raise NotFoundError(f"Category with id {category_id} not found")

        stmt = (
            select(ReceiptItem)
            .where(ReceiptItem.category_id == category_id)
            .offset(skip)
            .limit(limit)
        )
        results = await self.session.scalars(stmt)
        return results.all()

import os
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import UploadFile
from PIL import Image
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.category.models import CategoryCreate
from app.category.services import CategoryService
from app.core.config import settings
from app.core.decorators import transactional
from app.core.exceptions import BadRequestError, NotFoundError, ServiceUnavailableError
from app.integrations.pydantic_ai.receipt_agent import analyze_receipt

from .models import (
    Receipt,
    ReceiptCreate,
    ReceiptItem,
    ReceiptItemCreate,
    ReceiptItemCreateRequest,
    ReceiptItemUpdate,
    ReceiptUpdate,
)


class ReceiptService:
    """Service for managing receipts and receipt items."""

    def __init__(
        self,
        session: AsyncSession,
        category_service: CategoryService,
    ) -> None:
        self.session = session
        self.category_service = category_service

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
        image_path = settings.UPLOAD_DIR / unique_filename

        # Save the uploaded file
        with open(image_path, "wb") as f:
            content = await image_file.read()
            f.write(content)

        # Open and validate the image
        try:
            pil_image = Image.open(image_path)
            pil_image.verify()  # Verify it's a valid image
            pil_image = Image.open(image_path)  # Re-open after verify
        except Exception as e:
            raise BadRequestError(f"Invalid image file: {e}") from e

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
            if receipt.id is None:
                raise ServiceUnavailableError(
                    "Failed to create receipt - ID not assigned"
                )

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
            for item in receipt_items:
                self.session.add(item)
            await self.session.flush()

            # Get the updated receipt with items
            if receipt.id is None:
                raise ServiceUnavailableError("Failed to create receipt")
            return await self.get(receipt.id)

        except Exception as e:
            raise ServiceUnavailableError(f"Failed to analyze receipt: {str(e)}") from e

    async def get(self, receipt_id: int) -> Receipt:
        """Get a receipt by ID."""
        stmt = select(Receipt).where(Receipt.id == receipt_id)
        receipt = await self.session.scalar(stmt)

        if not receipt:
            raise NotFoundError(f"Receipt with id {receipt_id} not found")

        # Ensure items are loaded
        await self.session.refresh(receipt, ["items"])

        return receipt

    async def list(self, *, skip: int = 0, limit: int = 100) -> Sequence[Receipt]:
        """List all receipts with pagination."""
        stmt = select(Receipt).offset(skip).limit(limit)
        results = await self.session.exec(stmt)
        receipts = results.all()

        # Ensure items are loaded for each receipt
        for receipt in receipts:
            await self.session.refresh(receipt, ["items"])

        return receipts

    async def update(self, receipt_id: int, receipt_in: ReceiptUpdate) -> Receipt:
        """Update a receipt."""
        # Get the receipt from the database
        receipt = await self.get(receipt_id)

        # Prepare update data
        update_data = receipt_in.model_dump(exclude_unset=True, exclude={"id"})

        # Update the receipt
        receipt.sqlmodel_update(update_data)
        receipt.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(receipt, ["items"])

        return receipt

    async def delete(self, receipt_id: int) -> None:
        """Delete a receipt."""
        receipt = await self.get(receipt_id)
        await self.session.delete(receipt)
        await self.session.flush()

    # Receipt Item Operations

    async def update_item(
        self, receipt_id: int, item_id: int, item_in: ReceiptItemUpdate
    ) -> Receipt:
        """Update a receipt item."""
        # Get the receipt to verify it exists
        receipt = await self.get(receipt_id)

        # Find the item in the receipt
        item = next((i for i in receipt.items if i.id == item_id), None)
        if not item:
            raise NotFoundError(
                f"Item with id {item_id} not found in receipt {receipt_id}"
            )

        # Update item fields
        update_data = item_in.model_dump(exclude_unset=True)
        item.sqlmodel_update(update_data)
        item.updated_at = datetime.now(UTC)

        await self.session.flush()
        await self.session.refresh(receipt, ["items"])

        return receipt

    async def create_items(
        self, receipt_id: int, items_in: Sequence[ReceiptItemCreate]
    ) -> Sequence[ReceiptItem]:
        """Create multiple receipt items."""
        # Get the receipt from the database
        receipt = await self.get(receipt_id)

        items = [ReceiptItem(**item.model_dump()) for item in items_in]
        for item in items:
            if receipt.id is not None:
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
        results = await self.session.exec(stmt)
        return results.all()

    async def create_item(
        self, receipt_id: int, item_in: ReceiptItemCreateRequest
    ) -> Receipt:
        """Create a single receipt item and update the receipt total.

        Args:
            receipt_id: The ID of the receipt to add the item to
            item_in: The item data

        Returns:
            The updated receipt with all items
        """
        # Get receipt with row lock to prevent concurrent update race conditions
        stmt = select(Receipt).where(Receipt.id == receipt_id).with_for_update()
        receipt = await self.session.scalar(stmt)
        if not receipt:
            raise NotFoundError(f"Receipt with id {receipt_id} not found")

        # Validate currency matches the receipt
        if item_in.currency != receipt.currency:
            raise BadRequestError(
                f"Item currency '{item_in.currency}' does not match "
                f"receipt currency '{receipt.currency}'"
            )

        # Calculate total_price from quantity and unit_price
        total_price = item_in.quantity * item_in.unit_price

        # Create the new item
        item = ReceiptItem(
            name=item_in.name,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price,
            total_price=total_price,
            currency=item_in.currency,
            category_id=item_in.category_id,
            receipt_id=receipt_id,
        )

        self.session.add(item)

        # Update the receipt total
        receipt.total_amount = receipt.total_amount + total_price
        receipt.updated_at = datetime.now(UTC)

        await self.session.flush()
        await self.session.refresh(receipt, ["items"])

        return receipt

    async def delete_item(self, receipt_id: int, item_id: int) -> Receipt:
        """Delete a receipt item and update the receipt total.

        Args:
            receipt_id: The ID of the receipt
            item_id: The ID of the item to delete

        Returns:
            The updated receipt with remaining items
        """
        # Get receipt with row lock to prevent concurrent update race conditions
        stmt = select(Receipt).where(Receipt.id == receipt_id).with_for_update()
        receipt = await self.session.scalar(stmt)
        if not receipt:
            raise NotFoundError(f"Receipt with id {receipt_id} not found")
        await self.session.refresh(receipt, ["items"])

        # Find the item in the receipt
        item = next((i for i in receipt.items if i.id == item_id), None)
        if not item:
            raise NotFoundError(
                f"Item with id {item_id} not found in receipt {receipt_id}"
            )

        # Update the receipt total before deleting
        receipt.total_amount = receipt.total_amount - item.total_price
        receipt.updated_at = datetime.now(UTC)

        # Delete the item
        await self.session.delete(item)
        await self.session.flush()
        await self.session.refresh(receipt, ["items"])

        return receipt

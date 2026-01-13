import os
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import TypedDict

from fastapi import UploadFile
from PIL import Image
from sqlmodel import col, select
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
    ReceiptItemUpdate,
    ReceiptUpdate,
)


class ReceiptFilters(TypedDict, total=False):
    """Filter parameters for listing receipts."""

    search: str | None
    store: str | None
    after: datetime | None
    before: datetime | None
    category_ids: list[int] | None
    min_amount: Decimal | None
    max_amount: Decimal | None


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

            # Ensure receipt has an ID after creation
            if receipt.id is None:
                raise ServiceUnavailableError("Failed to create receipt")
            receipt_id = receipt.id

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
                    receipt_id=receipt_id,
                )
                receipt_items.append(receipt_item)

            # Add items to database
            for item in receipt_items:
                self.session.add(item)
            await self.session.flush()

            # Get the updated receipt with items
            return await self.get(receipt_id)

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

    async def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: ReceiptFilters | None = None,
    ) -> Sequence[Receipt]:
        """List all receipts with pagination and optional filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional dictionary of filter parameters:
                - search: ILIKE search on store_name
                - store: Exact match on store_name
                - after: Filter receipts on or after this date
                - before: Filter receipts on or before this date
                - category_ids: Filter by category IDs (receipts with items in these categories)
                - min_amount: Minimum total_amount
                - max_amount: Maximum total_amount

        Returns:
            List of receipts matching the filters
        """
        # Build base query
        stmt = select(Receipt)

        # Apply filters if provided
        if filters:
            # Search filter (case-insensitive partial match on store_name)
            if search := filters.get("search"):
                stmt = stmt.where(col(Receipt.store_name).ilike(f"%{search}%"))

            # Exact store name match
            if store := filters.get("store"):
                stmt = stmt.where(col(Receipt.store_name) == store)

            # Date range filters
            if after := filters.get("after"):
                stmt = stmt.where(col(Receipt.purchase_date) >= after)
            if before := filters.get("before"):
                stmt = stmt.where(col(Receipt.purchase_date) <= before)

            # Amount range filters
            if (min_amount := filters.get("min_amount")) is not None:
                stmt = stmt.where(col(Receipt.total_amount) >= min_amount)
            if (max_amount := filters.get("max_amount")) is not None:
                stmt = stmt.where(col(Receipt.total_amount) <= max_amount)

            # Category filter (join with items table)
            if category_ids := filters.get("category_ids"):
                stmt = (
                    stmt.join(ReceiptItem)
                    .where(col(ReceiptItem.category_id).in_(category_ids))
                    .distinct()
                )

        # Apply pagination and ordering (newest first)
        stmt = stmt.order_by(col(Receipt.purchase_date).desc()).offset(skip).limit(limit)

        results = await self.session.scalars(stmt)
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
        results = await self.session.scalars(stmt)
        return results.all()

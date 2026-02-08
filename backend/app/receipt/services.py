import csv
import os
import uuid
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from io import StringIO
from pathlib import Path
from typing import TypedDict

from fastapi import UploadFile
from PIL import Image
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.category.models import CategoryCreate
from app.category.services import CategoryService
from app.core.config import settings
from app.core.exceptions import BadRequestError, NotFoundError, ServiceUnavailableError
from app.integrations.pydantic_ai.receipt_agent import analyze_receipt
from app.integrations.pydantic_ai.receipt_reconcile_agent import (
    analyze_reconciliation,
)
from app.receipt.exporters import ReceiptPDFGenerator
from app.receipt.models import (
    Receipt,
    ReceiptCreate,
    ReceiptItem,
    ReceiptItemAdjustment,
    ReceiptItemCreate,
    ReceiptItemCreateRequest,
    ReceiptItemUpdate,
    ReceiptRead,
    ReceiptReconcileSuggestion,
    ReceiptUpdate,
    ScanRemovedItem,
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


CentsList = list[int]
ReceiptItemList = list[ReceiptItem]
ReceiptItemAdjustmentList = list[ReceiptItemAdjustment]


class ReceiptService:
    """Service for managing receipts and receipt items."""

    def __init__(
        self,
        session: AsyncSession,
        category_service: CategoryService,
    ) -> None:
        self.session = session
        self.category_service = category_service

    def _recalculate_total(self, receipt: Receipt) -> Decimal:
        """Recalculate receipt total from item totals."""
        return sum((item.total_price for item in receipt.items), Decimal("0"))

    @staticmethod
    def _to_cents(amount: Decimal) -> int:
        """Convert a decimal amount to integer cents."""
        return int((amount * 100).quantize(Decimal("1")))

    @staticmethod
    def _is_better_subset(
        candidate: tuple[int, int, tuple[int, ...]],
        current: tuple[int, int, tuple[int, ...]],
    ) -> bool:
        """Compare subset candidates by count first, then by earlier-line preference."""
        candidate_count, candidate_score, _ = candidate
        current_count, current_score, _ = current
        if candidate_count != current_count:
            return candidate_count > current_count
        return candidate_score > current_score

    def _find_subset_indices_matching_total(
        self, item_totals_cents: CentsList, target_cents: int
    ) -> set[int] | None:
        """Find subset indices that sum exactly to target cents.

        Returns the highest-confidence subset by:
        1. Keeping the most lines
        2. Preferring earlier lines when counts tie
        """
        n_items = len(item_totals_cents)
        best_by_sum: dict[int, tuple[int, int, tuple[int, ...]]] = {0: (0, 0, ())}

        for idx, amount_cents in enumerate(item_totals_cents):
            existing_states = list(best_by_sum.items())
            for current_sum, state in existing_states:
                next_sum = current_sum + amount_cents
                if next_sum > target_cents:
                    continue

                count, score, indices = state
                # Larger score means the subset keeps earlier lines.
                candidate = (count + 1, score + (n_items - idx), indices + (idx,))
                current_best = best_by_sum.get(next_sum)
                if current_best is None or self._is_better_subset(
                    candidate, current_best
                ):
                    best_by_sum[next_sum] = candidate

        result = best_by_sum.get(target_cents)
        if result is None:
            return None
        return set(result[2])

    def _dedupe_scanned_items_by_total(
        self,
        items: ReceiptItemList,
        expected_total: Decimal,
        *,
        tolerance: Decimal = Decimal("0.05"),
    ) -> tuple[ReceiptItemList, ReceiptItemList, str | None]:
        """Drop clearly duplicated OCR lines when item sum exceeds receipt total.

        The heuristic only applies when:
        - an exact subset matches receipt total, and
        - every removed line has at least one duplicate signature.
        """
        if not items:
            return items, [], None

        item_totals_cents = [self._to_cents(item.total_price) for item in items]
        current_total_cents = sum(item_totals_cents)
        expected_total_cents = self._to_cents(expected_total)
        tolerance_cents = self._to_cents(tolerance)

        if abs(current_total_cents - expected_total_cents) <= tolerance_cents:
            return items, [], None
        if current_total_cents <= expected_total_cents:
            return items, [], None

        # Guard runtime for very large receipts.
        if len(items) > 120 or expected_total_cents > 500_000:
            return items, [], None

        keep_indices = self._find_subset_indices_matching_total(
            item_totals_cents, expected_total_cents
        )
        if not keep_indices or len(keep_indices) == len(items):
            return items, [], None

        removed_indices = sorted(set(range(len(items))) - keep_indices)
        signatures = [
            (
                item.name.strip().upper(),
                self._to_cents(item.total_price),
                item.currency,
            )
            for item in items
        ]
        signature_counts = Counter(signatures)

        # Only auto-drop lines that look duplicated in extracted output.
        if any(signature_counts[signatures[idx]] < 2 for idx in removed_indices):
            return items, [], None

        filtered_items = [items[idx] for idx in sorted(keep_indices)]
        removed_items = [items[idx] for idx in removed_indices]
        filtered_total_cents = sum(
            self._to_cents(item.total_price) for item in filtered_items
        )
        if abs(filtered_total_cents - expected_total_cents) > tolerance_cents:
            return items, [], None

        note = (
            f"Auto-removed {len(removed_indices)} likely duplicate line(s) "
            "to align item sum with receipt total."
        )
        return filtered_items, removed_items, note

    def _fallback_duplicate_removal_adjustments(
        self, items: ReceiptItemList, expected_total: Decimal
    ) -> tuple[ReceiptItemAdjustmentList, str | None]:
        """Build deterministic remove-adjustments when AI returns no actionable output."""
        _, removed_items, note = self._dedupe_scanned_items_by_total(
            items, expected_total
        )
        adjustments: ReceiptItemAdjustmentList = []
        for item in removed_items:
            if item.id is None:
                continue
            adjustments.append(
                ReceiptItemAdjustment(
                    item_id=item.id,
                    remove=True,
                    reason="Likely duplicated OCR line based on repeated signatures and total mismatch.",
                )
            )
        return adjustments, note

    @staticmethod
    def _normalize_reconcile_reason(reason: str | None) -> str:
        """Normalize reconcile reasons to a concise single sentence for UI."""
        if not reason:
            return "Likely duplicate/noise line."
        compact = " ".join(reason.replace("\n", " ").split())
        if ". " in compact:
            compact = compact.split(". ", 1)[0]
        if len(compact) > 180:
            compact = f"{compact[:177].rstrip()}..."
        return compact

    def resolve_image_path(self, image_path: str) -> Path:
        """Resolve and validate receipt image path within upload directory."""
        upload_root = settings.UPLOAD_DIR.resolve()
        upload_dir = settings.UPLOAD_DIR
        path = Path(image_path)

        if path.is_absolute():
            candidate = path
        elif (
            upload_dir.parts and path.parts[: len(upload_dir.parts)] == upload_dir.parts
        ):
            candidate = (Path.cwd() / path).resolve(strict=False)
        else:
            candidate = (upload_root / path).resolve(strict=False)

        resolved = candidate.resolve(strict=False)

        if upload_root not in resolved.parents and resolved != upload_root:
            raise NotFoundError("Receipt image not found")
        if not resolved.exists() or not resolved.is_file():
            raise NotFoundError("Receipt image not found")

        return resolved

    async def create(self, receipt_in: ReceiptCreate, user_id: int) -> Receipt:
        """Create a new receipt."""
        receipt = Receipt(**receipt_in.model_dump(), user_id=user_id)
        self.session.add(receipt)
        await self.session.flush()
        return receipt

    async def create_from_scan(
        self, image_file: UploadFile, user_id: int
    ) -> ReceiptRead:
        """Create a receipt from an uploaded image file.

        This method:
        1. Saves the uploaded image
        2. Processes the image with AI to extract receipt data
        3. Creates categories if they don't exist
        4. Creates the receipt and its items

        If any step fails, the saved image file is cleaned up.

        Args:
            image_file: The uploaded receipt image

        Returns:
            The created receipt with all its items
        """
        # Generate unique filename for the image
        file_ext = os.path.splitext(image_file.filename or "receipt.jpg")[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        image_path = settings.UPLOAD_DIR / unique_filename

        try:
            # Save the uploaded file with size enforcement
            max_bytes = settings.max_upload_size_bytes
            bytes_read = 0
            with open(image_path, "wb") as f:
                while True:
                    chunk = await image_file.read(1024 * 1024)
                    if not chunk:
                        break
                    bytes_read += len(chunk)
                    if bytes_read > max_bytes:
                        raise BadRequestError(
                            f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB."
                        )
                    f.write(chunk)

            # Open and validate the image
            try:
                pil_image = Image.open(image_path)
                pil_image.verify()  # Verify it's a valid image
                pil_image = Image.open(image_path)  # Re-open after verify
            except Exception as e:
                raise BadRequestError(f"Invalid image file: {e}") from e

            # Get existing categories to help the AI model
            categories = await self.category_service.list(user_id=user_id)
            category_dicts = [
                {"name": cat.name, "description": cat.description or ""}
                for cat in categories
            ]

            # Analyze the receipt with AI
            try:
                receipt_data = await analyze_receipt(pil_image, category_dicts)
            except Exception as e:
                raise ServiceUnavailableError(f"Failed to analyze receipt: {e}") from e

            # Create receipt record
            receipt_create = ReceiptCreate(
                store_name=receipt_data.store_name,
                total_amount=Decimal(str(receipt_data.total_amount)),
                currency=receipt_data.currency,
                purchase_date=receipt_data.date,
                image_path=str(image_path),
            )

            receipt = await self.create(receipt_create, user_id=user_id)
            if receipt.id is None:
                raise ServiceUnavailableError(
                    "Failed to create receipt - ID not assigned"
                )
            receipt_id = receipt.id

            # Process each item
            receipt_items: list[ReceiptItem] = []
            for item_data in receipt_data.items:
                # Get or create category
                category = await self.category_service.get_by_name(
                    item_data.category.name, user_id=user_id
                )
                if not category:
                    category_create = CategoryCreate(
                        name=item_data.category.name,
                        description=item_data.category.description,
                    )
                    category = await self.category_service.create(
                        category_create, user_id=user_id
                    )

                # Calculate quantity and prices (guard against zero/negative from AI)
                raw_quantity = item_data.quantity if item_data.quantity >= 1 else 1
                quantity = int(raw_quantity) if raw_quantity.is_integer() else 1

                # Round to 2 decimal places to avoid floating point precision issues
                unit_price = round(item_data.price / raw_quantity, 2)
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
            receipt_items, removed_items, auto_note = (
                self._dedupe_scanned_items_by_total(receipt_items, receipt.total_amount)
            )
            if auto_note:
                receipt.notes = (
                    f"{receipt.notes}\n{auto_note}".strip()
                    if receipt.notes
                    else auto_note
                )

            for item in receipt_items:
                self.session.add(item)
            await self.session.flush()

            # Get the updated receipt with items
            scanned_receipt = await self.get(receipt_id, user_id=user_id)
            scan_response = ReceiptRead.model_validate(scanned_receipt)
            if removed_items:
                scan_response.scan_removed_items = [
                    ScanRemovedItem(
                        name=item.name,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        total_price=item.total_price,
                        currency=item.currency,
                        category_id=item.category_id,
                    )
                    for item in removed_items
                ]
            return scan_response

        except Exception:
            # Clean up the saved file on any failure
            if image_path.exists():
                image_path.unlink()
            raise

    async def get(self, receipt_id: int, user_id: int) -> Receipt:
        """Get a receipt by ID."""
        stmt = select(Receipt).where(
            Receipt.id == receipt_id, col(Receipt.user_id) == user_id
        )
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
        limit: int | None = 100,
        filters: ReceiptFilters | None = None,
        user_id: int,
    ) -> Sequence[Receipt]:
        """List all receipts with pagination and optional filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return (None for no limit)
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
        # Build base query (items are eagerly loaded via relationship's lazy="selectin")
        stmt = select(Receipt).where(col(Receipt.user_id) == user_id)

        # Apply filters if provided
        if filters:
            # Search filter (case-insensitive partial match on store_name)
            if search := filters.get("search"):
                # Escape SQL LIKE wildcards to prevent unexpected matches
                escaped_search = (
                    search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                )
                stmt = stmt.where(
                    col(Receipt.store_name).ilike(f"%{escaped_search}%", escape="\\")
                )

            # Exact store name match
            if store := filters.get("store"):
                stmt = stmt.where(col(Receipt.store_name) == store)

            # Date range filters
            if after := filters.get("after"):
                stmt = stmt.where(col(Receipt.purchase_date) >= after)
            if before := filters.get("before"):
                # Add 1 day to include entire selected day (before comes as midnight)
                stmt = stmt.where(
                    col(Receipt.purchase_date) < before + timedelta(days=1)
                )

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
        stmt = stmt.order_by(col(Receipt.purchase_date).desc()).offset(skip)
        if limit is not None:
            stmt = stmt.limit(limit)

        results = await self.session.exec(stmt)
        return results.all()

    async def list_stores(self, user_id: int) -> Sequence[str]:
        """Get a list of unique store names for a specific user.

        Args:
            user_id: The ID of the user whose stores to retrieve.

        Returns:
            Sorted list of unique store names from the user's receipts.
        """
        stmt = (
            select(Receipt.store_name)
            .where(col(Receipt.user_id) == user_id)
            .distinct()
            .order_by(Receipt.store_name)
        )
        results = await self.session.exec(stmt)
        return results.all()

    async def update(
        self, receipt_id: int, receipt_in: ReceiptUpdate, user_id: int
    ) -> Receipt:
        """Update a receipt."""
        # Get the receipt from the database
        receipt = await self.get(receipt_id, user_id)

        # Prepare update data
        update_data = receipt_in.model_dump(exclude_unset=True, exclude={"id"})

        # Coerce null tags to empty list (DB column is NOT NULL)
        if "tags" in update_data and update_data["tags"] is None:
            update_data["tags"] = []

        # Update the receipt
        receipt.sqlmodel_update(update_data)
        receipt.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(receipt, ["items"])

        return receipt

    async def delete(self, receipt_id: int, user_id: int) -> None:
        """Delete a receipt."""
        receipt = await self.get(receipt_id, user_id)
        await self.session.delete(receipt)
        await self.session.flush()

    # Receipt Item Operations

    async def update_item(
        self, receipt_id: int, item_id: int, item_in: ReceiptItemUpdate, user_id: int
    ) -> Receipt:
        """Update a receipt item."""
        # Get the receipt to verify it exists
        receipt = await self.get(receipt_id, user_id)

        # Find the item in the receipt
        item = next((i for i in receipt.items if i.id == item_id), None)
        if not item:
            raise NotFoundError(
                f"Item with id {item_id} not found in receipt {receipt_id}"
            )

        # Update item fields
        update_data = item_in.model_dump(exclude_unset=True)
        item.sqlmodel_update(update_data)
        item.total_price = item.unit_price * item.quantity
        item.updated_at = datetime.now(UTC)

        receipt.updated_at = datetime.now(UTC)

        await self.session.flush()
        await self.session.refresh(receipt, ["items"])

        return receipt

    async def reconcile_items(
        self, receipt_id: int, user_id: int
    ) -> ReceiptReconcileSuggestion:
        """Suggest AI-based adjustments to reconcile items with receipt total."""
        receipt = await self.get(receipt_id, user_id)

        if not receipt.items:
            raise BadRequestError("Receipt has no items to reconcile")

        receipt_total = Decimal(str(receipt.total_amount))
        items_total = sum((item.total_price for item in receipt.items), Decimal("0"))
        difference = items_total - receipt_total

        if abs(difference) <= Decimal("0.05"):
            return ReceiptReconcileSuggestion(
                receipt_id=receipt_id,
                receipt_total=receipt_total,
                items_total=items_total,
                difference=difference,
                adjusted_items_total=items_total,
                remaining_difference=Decimal("0"),
                adjustments=[],
                notes="Items already match receipt total.",
            )

        # Load receipt image for AI reconciliation
        image_path = self.resolve_image_path(receipt.image_path)
        try:
            image = Image.open(image_path)
        except Exception as e:
            raise BadRequestError(f"Invalid receipt image: {e}") from e

        items_context: list[dict[str, str | int | Decimal]] = []
        for item in receipt.items:
            if item.id is None:
                raise ServiceUnavailableError("Receipt item missing ID")
            items_context.append(
                {
                    "id": item.id,
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price,
                    "currency": item.currency,
                }
            )

        analysis = await analyze_reconciliation(
            image=image,
            receipt_total=str(receipt_total),
            items=items_context,
        )

        notes: list[str] = []

        valid_item_ids = {item.id for item in receipt.items if item.id is not None}

        adjustments_by_id: dict[int, ReceiptItemAdjustment] = {}
        for adjustment in analysis.adjustments:
            if adjustment.item_id not in valid_item_ids:
                notes.append(
                    f"Ignored adjustment for unknown item id {adjustment.item_id}."
                )
                continue
            if adjustment.item_id in adjustments_by_id:
                notes.append(
                    f"Ignored duplicate adjustment for item id {adjustment.item_id}."
                )
                continue
            if not adjustment.remove:
                notes.append(
                    f"Ignored non-remove adjustment for item id {adjustment.item_id}."
                )
                continue
            adjustments_by_id[adjustment.item_id] = ReceiptItemAdjustment(
                item_id=adjustment.item_id,
                remove=True,
                reason=self._normalize_reconcile_reason(adjustment.reason),
            )

        if not adjustments_by_id and abs(difference) > Decimal("0.05"):
            fallback_adjustments, fallback_note = (
                self._fallback_duplicate_removal_adjustments(
                    list(receipt.items), receipt_total
                )
            )
            if fallback_adjustments:
                notes.append(
                    "Applied deterministic duplicate-line fallback because AI returned no actionable adjustments."
                )
                if fallback_note:
                    notes.append(fallback_note)
                adjustments_by_id.update(
                    {
                        adjustment.item_id: adjustment
                        for adjustment in fallback_adjustments
                    }
                )

        # Validate adjustments and compute adjusted total
        adjusted_total = Decimal("0")
        for item in receipt.items:
            if item.id is None:
                raise ServiceUnavailableError("Receipt item missing ID")
            adjustment = adjustments_by_id.get(item.id)
            if adjustment and adjustment.remove:
                continue
            adjusted_total += item.total_price

        remaining_difference = adjusted_total - receipt_total
        if abs(remaining_difference) > Decimal("0.05"):
            notes.append(
                "AI suggestions did not fully reconcile the total. "
                f"Remaining difference: {remaining_difference}"
            )

        if not adjustments_by_id and abs(difference) > Decimal("0.05"):
            notes.append("AI did not provide actionable adjustments.")

        notes_text = " ".join(notes) if notes else None

        return ReceiptReconcileSuggestion(
            receipt_id=receipt_id,
            receipt_total=receipt_total,
            items_total=items_total,
            difference=difference,
            adjusted_items_total=adjusted_total,
            remaining_difference=remaining_difference,
            adjustments=list(adjustments_by_id.values()),
            notes=notes_text,
        )

    async def create_items(
        self, receipt_id: int, items_in: Sequence[ReceiptItemCreate], user_id: int
    ) -> Sequence[ReceiptItem]:
        """Create multiple receipt items."""
        # Get the receipt from the database
        receipt = await self.get(receipt_id, user_id=user_id)

        items = [ReceiptItem(**item.model_dump()) for item in items_in]
        for item in items:
            if receipt.id is not None:
                item.receipt_id = receipt.id
            self.session.add(item)

        await self.session.flush()
        return items

    async def list_items_by_category(
        self, category_id: int, user_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[ReceiptItem]:
        """List receipt items by category for a specific user.

        Args:
            category_id: The ID of the category to filter by.
            user_id: The ID of the user whose items to retrieve.
            skip: Number of items to skip.
            limit: Maximum number of items to return.

        Returns:
            List of receipt items belonging to the user's receipts in the specified category.

        Raises:
            NotFoundError: If the category doesn't exist or doesn't belong to the user.
        """
        # Verify the category exists and belongs to the user
        category = await self.category_service.get(category_id, user_id)
        if not category:
            raise NotFoundError(f"Category with id {category_id} not found")

        # Join with Receipt table to filter by user_id
        stmt = (
            select(ReceiptItem)
            .join(Receipt, col(ReceiptItem.receipt_id) == col(Receipt.id))
            .where(ReceiptItem.category_id == category_id)
            .where(col(Receipt.user_id) == user_id)
            .offset(skip)
            .limit(limit)
        )
        results = await self.session.exec(stmt)
        return results.all()

    async def create_item(
        self, receipt_id: int, item_in: ReceiptItemCreateRequest, user_id: int
    ) -> Receipt:
        """Create a single receipt item.

        Args:
            receipt_id: The ID of the receipt to add the item to
            item_in: The item data
            user_id: The ID of the user (for ownership verification)

        Returns:
            The updated receipt with all items
        """
        # Get receipt with row lock to prevent concurrent update race conditions
        stmt = (
            select(Receipt)
            .where(Receipt.id == receipt_id, col(Receipt.user_id) == user_id)
            .with_for_update()
        )
        receipt = await self.session.scalar(stmt)
        if not receipt:
            raise NotFoundError(f"Receipt with id {receipt_id} not found")
        await self.session.refresh(receipt, ["items"])

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

        receipt.items.append(item)
        receipt.updated_at = datetime.now(UTC)

        await self.session.flush()
        await self.session.refresh(receipt, ["items"])

        return receipt

    async def delete_item(self, receipt_id: int, item_id: int, user_id: int) -> Receipt:
        """Delete a receipt item.

        Args:
            receipt_id: The ID of the receipt
            item_id: The ID of the item to delete
            user_id: The ID of the user (for ownership verification)

        Returns:
            The updated receipt with remaining items
        """
        # Get receipt with row lock to prevent concurrent update race conditions
        stmt = (
            select(Receipt)
            .where(Receipt.id == receipt_id, col(Receipt.user_id) == user_id)
            .with_for_update()
        )
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

        if item in receipt.items:
            receipt.items.remove(item)

        # Delete the item
        await self.session.delete(item)
        await self.session.flush()
        await self.session.refresh(receipt, ["items"])

        receipt.updated_at = datetime.now(UTC)

        return receipt

    async def export_to_csv(
        self, *, filters: ReceiptFilters | None = None, user_id: int
    ) -> str:
        """Export receipts to CSV format.

        Args:
            filters: Optional dictionary of filter parameters (same as list method)
            user_id: The ID of the user whose receipts to export

        Returns:
            CSV content as a string with RFC 4180 compliance

        Note:
            The CSV format flattens receipt data: one row per item.
            Receipts without items will have one row with empty item fields.
        """
        # Get filtered receipts using existing list method
        # Note: No limit applied to ensure complete export of all matching receipts
        receipts = await self.list(filters=filters, user_id=user_id, skip=0, limit=None)

        # Define CSV columns
        fieldnames = [
            "receipt_id",
            "receipt_date",
            "store_name",
            "receipt_total",
            "receipt_currency",
            "payment_method",
            "tax_amount",
            "item_id",
            "item_name",
            "item_quantity",
            "item_unit_price",
            "item_total_price",
            "item_currency",
            "category_name",
        ]

        # Use StringIO for in-memory CSV generation
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        # Write data rows
        for receipt in receipts:
            # Build base row with common receipt fields
            base_row = {
                "receipt_id": receipt.id,
                "receipt_date": receipt.purchase_date.isoformat(),
                "store_name": receipt.store_name,
                "receipt_total": str(receipt.total_amount),
                "receipt_currency": receipt.currency,
                "payment_method": receipt.payment_method.value
                if receipt.payment_method
                else "",
                "tax_amount": str(receipt.tax_amount)
                if receipt.tax_amount is not None
                else "",
            }

            # Handle receipts with no items
            if not receipt.items:
                writer.writerow(
                    {
                        **base_row,
                        "item_id": "",
                        "item_name": "",
                        "item_quantity": "",
                        "item_unit_price": "",
                        "item_total_price": "",
                        "item_currency": "",
                        "category_name": "",
                    }
                )
            else:
                # One row per item, with receipt data repeated
                for item in receipt.items:
                    writer.writerow(
                        {
                            **base_row,
                            "item_id": item.id,
                            "item_name": item.name,
                            "item_quantity": item.quantity,
                            "item_unit_price": str(item.unit_price),
                            "item_total_price": str(item.total_price),
                            "item_currency": item.currency,
                            "category_name": item.category.name
                            if item.category
                            else "",
                        }
                    )

        return output.getvalue()

    async def export_to_pdf(
        self,
        *,
        filters: ReceiptFilters | None = None,
        user_id: int,
        include_images: bool = False,
    ) -> bytes:
        """Export receipts to PDF format.

        Args:
            filters: Optional dictionary of filter parameters (same as list method)
            user_id: The ID of the user whose receipts to export
            include_images: Whether to include receipt images in the PDF

        Returns:
            PDF file content as bytes

        Note:
            The PDF includes a summary section with overall statistics and category
            breakdown, followed by detailed sections for each receipt with items table.
            Receipt images are optionally embedded if include_images is True.
        """
        # Get filtered receipts using existing list method
        # Note: No limit applied to ensure complete export of all matching receipts
        receipts = await self.list(filters=filters, user_id=user_id, skip=0, limit=None)

        # Generate PDF using the PDF generator
        generator = ReceiptPDFGenerator()
        pdf_bytes = generator.generate(list(receipts), include_images=include_images)

        return pdf_bytes

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, File, Query, UploadFile, status

from .deps import ReceiptDeps
from .models import (
    Receipt,
    ReceiptItem,
    ReceiptItemCreateRequest,
    ReceiptItemRead,
    ReceiptItemUpdate,
    ReceiptRead,
    ReceiptUpdate,
)
from .services import ReceiptFilters

router = APIRouter(prefix="/api/v1/receipts", tags=["receipts"])


@router.post("/scan", response_model=ReceiptRead, status_code=status.HTTP_201_CREATED)
async def create_receipt_from_scan(
    *,
    service: ReceiptDeps,
    image: Annotated[UploadFile, File()],
) -> Receipt:
    """
    Upload and scan a receipt image.
    The image will be analyzed using AI to extract information.
    The receipt and items will be created in the database.
    """
    # Process receipt and create in database
    receipt = await service.create_from_scan(image)  # pragma: no cover
    return receipt  # pragma: no cover


@router.get("", response_model=list[ReceiptRead], status_code=status.HTTP_200_OK)
async def list_receipts(
    service: ReceiptDeps,
    skip: int = 0,
    limit: int = 100,
    search: Annotated[
        str | None,
        Query(description="Search store name (case-insensitive partial match)"),
    ] = None,
    store: Annotated[
        str | None,
        Query(description="Exact store name match"),
    ] = None,
    after: Annotated[
        datetime | None,
        Query(description="Filter receipts on or after this date (ISO 8601 format)"),
    ] = None,
    before: Annotated[
        datetime | None,
        Query(description="Filter receipts on or before this date (ISO 8601 format)"),
    ] = None,
    category_ids: Annotated[
        list[int] | None,
        Query(
            description="Filter by category IDs (receipts with items in these categories)"
        ),
    ] = None,
    min_amount: Annotated[
        Decimal | None,
        Query(description="Minimum total amount", ge=0),
    ] = None,
    max_amount: Annotated[
        Decimal | None,
        Query(description="Maximum total amount", ge=0),
    ] = None,
) -> Sequence[Receipt]:
    """List all receipts with optional filtering.

    Filter options:
    - search: Case-insensitive partial match on store name
    - store: Exact store name match
    - after/before: Date range filter (ISO 8601 format)
    - category_ids: Filter receipts that have items in specified categories
    - min_amount/max_amount: Total amount range filter
    """
    # Build filters dict only with provided values
    filters: ReceiptFilters = {}
    if search is not None:
        filters["search"] = search
    if store is not None:
        filters["store"] = store
    if after is not None:
        filters["after"] = after
    if before is not None:
        filters["before"] = before
    if category_ids is not None:
        filters["category_ids"] = category_ids
    if min_amount is not None:
        filters["min_amount"] = min_amount
    if max_amount is not None:
        filters["max_amount"] = max_amount

    receipts = await service.list(skip=skip, limit=limit, filters=filters or None)
    return receipts  # pragma: no cover


@router.get("/stores", response_model=list[str], status_code=status.HTTP_200_OK)
async def list_stores(
    service: ReceiptDeps,
) -> Sequence[str]:
    """Get a list of unique store names for filtering."""
    return await service.list_stores()


@router.get("/{receipt_id}", response_model=ReceiptRead, status_code=status.HTTP_200_OK)
async def get_receipt(
    receipt_id: int,
    service: ReceiptDeps,
) -> Receipt:
    """Get a receipt by ID with all its items."""
    return await service.get(receipt_id)


@router.get(
    "/category/{category_id}/items",
    response_model=list[ReceiptItemRead],
    status_code=status.HTTP_200_OK,
)
async def list_items_by_category(
    category_id: int,
    service: ReceiptDeps,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[ReceiptItem]:
    """List all receipt items in a category."""
    return await service.list_items_by_category(
        category_id=category_id,
        skip=skip,
        limit=limit,
    )


@router.patch(
    "/{receipt_id}",
    response_model=ReceiptRead,
    status_code=status.HTTP_200_OK,
)
async def update_receipt(
    receipt_id: int,
    receipt_in: ReceiptUpdate,
    service: ReceiptDeps,
) -> Receipt:
    """Update a receipt."""
    return await service.update(receipt_id, receipt_in)


@router.delete("/{receipt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_receipt(
    receipt_id: int,
    service: ReceiptDeps,
) -> None:
    """Delete a receipt and all its items."""
    await service.delete(receipt_id)


@router.patch(
    "/{receipt_id}/items/{item_id}",
    response_model=ReceiptRead,
    status_code=status.HTTP_200_OK,
)
async def update_receipt_item(
    receipt_id: int,
    item_id: int,
    item_in: ReceiptItemUpdate,
    service: ReceiptDeps,
) -> Receipt:
    """Update a receipt item."""
    return await service.update_item(receipt_id, item_id, item_in)


@router.post(
    "/{receipt_id}/items",
    response_model=ReceiptRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_receipt_item(
    receipt_id: int,
    item_in: ReceiptItemCreateRequest,
    service: ReceiptDeps,
) -> Receipt:
    """Create a new item for a receipt.

    Creates the item and updates the receipt total automatically.
    """
    return await service.create_item(receipt_id, item_in)


@router.delete(
    "/{receipt_id}/items/{item_id}",
    response_model=ReceiptRead,
    status_code=status.HTTP_200_OK,
)
async def delete_receipt_item(
    receipt_id: int,
    item_id: int,
    service: ReceiptDeps,
) -> Receipt:
    """Delete a receipt item.

    Deletes the item and updates the receipt total automatically.
    Returns the updated receipt with remaining items.
    """
    return await service.delete_item(receipt_id, item_id)

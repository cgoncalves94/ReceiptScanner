import mimetypes
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, File, Query, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse

from app.auth.deps import CurrentUser, CurrentUserFromRequest, require_user_id
from app.receipt.deps import ReceiptDeps
from app.receipt.models import (
    Receipt,
    ReceiptItem,
    ReceiptItemCreateRequest,
    ReceiptItemRead,
    ReceiptItemUpdate,
    ReceiptRead,
    ReceiptUpdate,
)
from app.receipt.services import ReceiptFilters

router = APIRouter(prefix="/api/v1/receipts", tags=["receipts"])


def build_receipt_filters(
    search: str | None,
    store: str | None,
    after: datetime | None,
    before: datetime | None,
    category_ids: list[int] | None,
    min_amount: Decimal | None,
    max_amount: Decimal | None,
) -> ReceiptFilters:
    """Build a ReceiptFilters dictionary from query parameters.

    Only includes parameters that are not None.

    Args:
        search: Search term for store name
        store: Exact store name match
        after: Filter receipts on or after this date
        before: Filter receipts on or before this date
        category_ids: Filter by category IDs
        min_amount: Minimum total amount
        max_amount: Maximum total amount

    Returns:
        Dictionary with only non-None filter values
    """
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
    return filters


@router.post("/scan", response_model=ReceiptRead, status_code=status.HTTP_201_CREATED)
async def create_receipt_from_scan(
    *,
    current_user: CurrentUser,
    service: ReceiptDeps,
    image: Annotated[UploadFile, File()],
) -> Receipt:
    """
    Upload and scan a receipt image.
    The image will be analyzed using AI to extract information.
    The receipt and items will be created in the database.
    """
    user_id = require_user_id(current_user)
    return await service.create_from_scan(image, user_id=user_id)


@router.get("", response_model=list[ReceiptRead], status_code=status.HTTP_200_OK)
async def list_receipts(
    current_user: CurrentUser,
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
    user_id = require_user_id(current_user)
    # Build filters dict using helper function
    filters = build_receipt_filters(
        search, store, after, before, category_ids, min_amount, max_amount
    )

    receipts = await service.list(
        skip=skip, limit=limit, filters=filters or None, user_id=user_id
    )
    return receipts  # pragma: no cover


@router.get("/export", status_code=status.HTTP_200_OK)
async def export_receipts(
    current_user: CurrentUser,
    service: ReceiptDeps,
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
) -> StreamingResponse:
    """Export receipts to CSV format with optional filtering.

    Returns a CSV file with all receipt and item data.
    Filter options are the same as list_receipts endpoint.
    """
    user_id = require_user_id(current_user)
    # Build filters dict using helper function
    filters = build_receipt_filters(
        search, store, after, before, category_ids, min_amount, max_amount
    )

    # Generate CSV content
    csv_content = await service.export_to_csv(filters=filters or None, user_id=user_id)

    # Generate filename with timestamp (UTC for consistency)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    filename = f"receipts_export_{timestamp}.csv"

    # Convert string to bytes for streaming
    csv_bytes = BytesIO(csv_content.encode("utf-8"))

    # Return streaming response with proper headers
    return StreamingResponse(
        csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/pdf", status_code=status.HTTP_200_OK)
async def export_receipts_pdf(
    current_user: CurrentUser,
    service: ReceiptDeps,
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
    include_images: Annotated[
        bool,
        Query(description="Include receipt images in the PDF"),
    ] = False,
) -> StreamingResponse:
    """Export receipts to PDF format with optional filtering.

    Returns a PDF file with all receipt and item data.
    Optionally includes receipt images when include_images=true.
    Filter options are the same as list_receipts endpoint.
    """
    user_id = require_user_id(current_user)
    # Build filters dict using helper function
    filters = build_receipt_filters(
        search, store, after, before, category_ids, min_amount, max_amount
    )

    # Generate PDF content
    pdf_content = await service.export_to_pdf(
        filters=filters or None, user_id=user_id, include_images=include_images
    )

    # Generate filename with timestamp (UTC for consistency)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    filename = f"receipts_export_{timestamp}.pdf"

    # Convert bytes to BytesIO for streaming
    pdf_bytes = BytesIO(pdf_content)

    # Return streaming response with proper headers
    return StreamingResponse(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/stores", response_model=list[str], status_code=status.HTTP_200_OK)
async def list_stores(
    current_user: CurrentUser,
    service: ReceiptDeps,
) -> Sequence[str]:
    """Get a list of unique store names for filtering."""
    user_id = require_user_id(current_user)
    return await service.list_stores(user_id=user_id)


@router.get("/{receipt_id}", response_model=ReceiptRead, status_code=status.HTTP_200_OK)
async def get_receipt(
    receipt_id: int,
    current_user: CurrentUser,
    service: ReceiptDeps,
) -> Receipt:
    """Get a receipt by ID with all its items."""
    user_id = require_user_id(current_user)
    return await service.get(receipt_id, user_id=user_id)


@router.get(
    "/{receipt_id}/image",
    status_code=status.HTTP_200_OK,
)
async def get_receipt_image(
    receipt_id: int,
    current_user: CurrentUserFromRequest,
    service: ReceiptDeps,
) -> FileResponse:
    """Get a receipt image for the current user."""
    user_id = require_user_id(current_user)
    receipt = await service.get(receipt_id, user_id=user_id)
    image_path = service.resolve_image_path(receipt.image_path)
    media_type, _ = mimetypes.guess_type(image_path.name)
    return FileResponse(image_path, media_type=media_type or "application/octet-stream")


@router.get(
    "/category/{category_id}/items",
    response_model=list[ReceiptItemRead],
    status_code=status.HTTP_200_OK,
)
async def list_items_by_category(
    category_id: int,
    current_user: CurrentUser,
    service: ReceiptDeps,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[ReceiptItem]:
    """List all receipt items in a category."""
    user_id = require_user_id(current_user)
    return await service.list_items_by_category(
        category_id=category_id,
        user_id=user_id,
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
    current_user: CurrentUser,
    service: ReceiptDeps,
) -> Receipt:
    """Update a receipt."""
    user_id = require_user_id(current_user)
    return await service.update(receipt_id, receipt_in, user_id=user_id)


@router.delete("/{receipt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_receipt(
    receipt_id: int,
    current_user: CurrentUser,
    service: ReceiptDeps,
) -> None:
    """Delete a receipt and all its items."""
    user_id = require_user_id(current_user)
    await service.delete(receipt_id, user_id=user_id)


@router.patch(
    "/{receipt_id}/items/{item_id}",
    response_model=ReceiptRead,
    status_code=status.HTTP_200_OK,
)
async def update_receipt_item(
    receipt_id: int,
    item_id: int,
    item_in: ReceiptItemUpdate,
    current_user: CurrentUser,
    service: ReceiptDeps,
) -> Receipt:
    """Update a receipt item."""
    user_id = require_user_id(current_user)
    return await service.update_item(receipt_id, item_id, item_in, user_id=user_id)


@router.post(
    "/{receipt_id}/items",
    response_model=ReceiptRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_receipt_item(
    receipt_id: int,
    item_in: ReceiptItemCreateRequest,
    current_user: CurrentUser,
    service: ReceiptDeps,
) -> Receipt:
    """Create a new item for a receipt.

    Creates the item and updates the receipt total automatically.
    """
    user_id = require_user_id(current_user)
    return await service.create_item(receipt_id, item_in, user_id=user_id)


@router.delete(
    "/{receipt_id}/items/{item_id}",
    response_model=ReceiptRead,
    status_code=status.HTTP_200_OK,
)
async def delete_receipt_item(
    receipt_id: int,
    item_id: int,
    current_user: CurrentUser,
    service: ReceiptDeps,
) -> Receipt:
    """Delete a receipt item.

    Deletes the item and updates the receipt total automatically.
    Returns the updated receipt with remaining items.
    """
    user_id = require_user_id(current_user)
    return await service.delete_item(receipt_id, item_id, user_id=user_id)

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status

from .deps import ReceiptDeps
from .models import (
    ReceiptItem,
    ReceiptRead,
    ReceiptUpdate,
)

router = APIRouter(prefix="/receipts", tags=["receipts"])


@router.post("/scan", response_model=ReceiptRead, status_code=status.HTTP_201_CREATED)
async def create_receipt_from_scan(
    *,
    service: ReceiptDeps,
    image: Annotated[UploadFile, File()],
) -> ReceiptRead:
    """
    Upload and scan a receipt image.
    The image will be analyzed using AI to extract information.
    The receipt and items will be created in the database.
    """
    # Check if service has a session
    if not hasattr(service, "session"):
        raise ValueError("Service has no session attribute")

    # Process receipt and create in database
    receipt = await service.create_from_scan(image)
    return receipt


@router.get("", response_model=list[ReceiptRead])
async def list_receipts(
    service: ReceiptDeps,
    skip: int = 0,
    limit: int = 100,
) -> list[ReceiptRead]:
    """List all receipts with their items."""
    receipts = await service.list(skip=skip, limit=limit)
    return receipts


@router.get("/{receipt_id}", response_model=ReceiptRead)
async def get_receipt(
    receipt_id: int,
    service: ReceiptDeps,
) -> ReceiptRead:
    """Get a receipt by ID with all its items."""
    return await service.get(receipt_id)


@router.get("/category/{category_id}/items", response_model=list[ReceiptItem])
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


@router.patch("/{receipt_id}", response_model=ReceiptRead)
async def update_receipt(
    receipt_id: int,
    receipt_in: ReceiptUpdate,
    service: ReceiptDeps,
) -> ReceiptRead:
    """Update a receipt."""
    return await service.update(receipt_id, receipt_in)

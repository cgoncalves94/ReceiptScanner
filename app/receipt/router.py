from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status

from .deps import ReceiptDeps
from .models import (
    Receipt,
    ReceiptItem,
    ReceiptItemRead,
    ReceiptRead,
    ReceiptUpdate,
)

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
) -> Sequence[Receipt]:
    """List all receipts with their items."""
    receipts = await service.list(skip=skip, limit=limit)
    return receipts  # pragma: no cover


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

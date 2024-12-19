import logging

from fastapi import APIRouter, File, UploadFile

from app.api.deps import CategoryServiceDep, ReceiptScannerDep, ReceiptServiceDep
from app.models import (
    ReceiptItemsByCategory,
    ReceiptsRead,
    ReceiptWithItemsRead,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/scan/", response_model=ReceiptWithItemsRead)
async def create_receipt_from_scan(
    service: ReceiptServiceDep,
    category_service: CategoryServiceDep,
    receipt_scanner: ReceiptScannerDep,
    file: UploadFile = File(...),
) -> ReceiptWithItemsRead:
    """
    Upload and scan a receipt image.
    The image will be processed and analyzed using AI to extract information.
    The receipt and items will be created in the database.

    """
    return await receipt_scanner.process_and_create_receipt(
        file=file,
        receipt_service=service,
        category_service=category_service,
    )


@router.get("/", response_model=ReceiptsRead)
async def list_receipts(
    service: ReceiptServiceDep,
    skip: int = 0,
    limit: int = 100,
) -> ReceiptsRead:
    """List all receipts with their items."""
    receipts = await service.list(skip=skip, limit=limit)
    return ReceiptsRead(data=receipts, count=len(receipts))


@router.get("/{receipt_id}", response_model=ReceiptWithItemsRead)
async def get_receipt(
    receipt_id: int,
    service: ReceiptServiceDep,
) -> ReceiptWithItemsRead:
    """Get a specific receipt by ID."""
    return await service.get_with_items(receipt_id=receipt_id)


@router.get(
    "/category/{category_id}/items", response_model=list[ReceiptItemsByCategory]
)
async def list_items_by_category(
    category_id: int,
    receipt_service: ReceiptServiceDep,
    category_service: CategoryServiceDep,
    skip: int = 0,
    limit: int = 100,
) -> list[ReceiptItemsByCategory]:
    """List all receipt items in a category."""
    # Verify category exists
    await category_service.get(category_id)
    return await receipt_service.list_items_by_category(
        category_id=category_id, skip=skip, limit=limit
    )

import shutil
from collections.abc import Sequence
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session

from app.api.deps import get_db
from app.integrations.scanner.receipt_scanner import ReceiptScanner
from app.models.receipt import Receipt
from app.schemas.receipt import ReceiptListResponse, ReceiptResponse
from app.services import ReceiptService

router = APIRouter()
receipt_scanner = ReceiptScanner()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/scan/", response_model=ReceiptResponse)
async def create_receipt_from_scan(
    file: UploadFile = File(...), db: Session = Depends(get_db)
) -> Receipt:
    """
    Upload and scan a receipt image.
    The image will be processed and analyzed using AI to extract information.
    """
    file_path = UPLOAD_DIR / file.filename
    try:
        # Save the uploaded file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process the receipt
        receipt, items_data, category_names = await receipt_scanner.scan_and_analyze(
            str(file_path)
        )

        # Use service layer to handle database operations
        receipt_service = ReceiptService(db)
        return receipt_service.create_receipt_with_items(receipt, items_data)

    except Exception as e:
        # Clean up the uploaded file in case of error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=500, detail=f"Error processing receipt: {str(e)}"
        )


@router.get("/", response_model=list[ReceiptListResponse])
def list_receipts(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> Sequence[Receipt]:
    """List all receipts with basic information (no items)."""
    receipt_service = ReceiptService(db)
    return receipt_service.list_receipts(skip, limit)


@router.get("/full/", response_model=list[ReceiptResponse])
def list_receipts_with_items(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> Sequence[Receipt]:
    """List all receipts with their items."""
    receipt_service = ReceiptService(db)
    return receipt_service.list_receipts_with_items(skip=skip, limit=limit)


@router.get("/{receipt_id}", response_model=ReceiptResponse)
def get_receipt(receipt_id: int, db: Session = Depends(get_db)) -> Receipt:
    """Get a specific receipt by ID."""
    receipt_service = ReceiptService(db)
    return receipt_service.get_receipt(receipt_id)

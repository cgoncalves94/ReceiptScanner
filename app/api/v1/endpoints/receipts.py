import logging
from collections.abc import Sequence

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.deps import CategoryServiceDep, ReceiptServiceDep
from app.core.config import settings
from app.exceptions import DomainException, ErrorCode
from app.integrations.scanner.receipt_scanner import ReceiptScanner
from app.schemas import (
    CategoryCreate,
    ReceiptCreate,
    ReceiptItemCreate,
    ReceiptItemsByCategory,
    ReceiptListResponse,
    ReceiptRead,
    ReceiptUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()
receipt_scanner = ReceiptScanner()


@router.post("/scan/", response_model=ReceiptRead)
async def create_receipt_from_scan(
    service: ReceiptServiceDep,
    category_service: CategoryServiceDep,
    file: UploadFile = File(...),
) -> ReceiptRead:
    """
    Upload and scan a receipt image.
    The image will be processed and analyzed using AI to extract information.
    """
    try:
        # Save and analyze receipt
        file_path = settings.UPLOADS_ORIGINAL_DIR / file.filename
        with file_path.open("wb") as buffer:
            content = await file.read()
            buffer.write(content)
            await file.seek(0)

        # Get existing categories to help with classification
        existing_categories = await category_service.list()
        existing_categories_dict = [
            {"name": cat.name, "description": cat.description}
            for cat in existing_categories
        ]

        try:
            analysis = await receipt_scanner.scan_and_analyze(
                str(file_path), existing_categories=existing_categories_dict
            )
        except DomainException as e:
            if e.code in (ErrorCode.VALIDATION_ERROR, ErrorCode.INTERNAL_ERROR):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=e.message,
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.message,
            )

        # First, create all necessary categories
        category_map = {}  # Store category_name -> category_id mapping
        for item in analysis.items:
            if item.category_name not in category_map:
                category = await category_service.get_by_name(item.category_name)
                if not category:
                    category = await category_service.create(
                        CategoryCreate(
                            name=item.category_name,
                            description=item.category_description,
                        )
                    )
                category_map[item.category_name] = category.id

        # Then create the receipt
        receipt = await service.create(
            ReceiptCreate(
                store_name=analysis.receipt.store_name,
                total_amount=analysis.receipt.total_amount,
                currency=analysis.receipt.currency,
                image_path=analysis.receipt.image_path,
                date=analysis.receipt.date,
            )
        )

        # Finally create all items with their category IDs
        items_in = [
            ReceiptItemCreate(
                name=item.name,
                price=item.price,
                quantity=item.quantity,
                currency=item.currency,
                category_id=category_map[item.category_name],
                receipt_id=receipt.id,
            )
            for item in analysis.items
        ]

        if items_in:
            await service.create_items(items_in)

        # Mark receipt as processed after successful item creation
        await service.update(receipt.id, ReceiptUpdate(processed=True))

        # Return complete receipt with items
        return await service.get_with_items(receipt.id)

    except Exception as e:
        logger.error(f"Error processing receipt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing receipt: {str(e)}",
        )


@router.get("/", response_model=list[ReceiptListResponse])
async def list_receipts(
    service: ReceiptServiceDep,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[ReceiptRead]:
    """List all receipts with basic information (no items)."""
    return await service.list(skip=skip, limit=limit)


@router.get("/full/", response_model=list[ReceiptRead])
async def list_receipts_with_items(
    service: ReceiptServiceDep,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[ReceiptRead]:
    """List all receipts with their items."""
    try:
        return await service.list_with_items(skip=skip, limit=limit)
    except DomainException as e:
        if e.code == ErrorCode.NOT_FOUND:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error listing receipts with items: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing receipts with items: {str(e)}",
        )


@router.get("/{receipt_id}", response_model=ReceiptRead)
async def get_receipt(
    receipt_id: int,
    service: ReceiptServiceDep,
) -> ReceiptRead:
    """Get a specific receipt by ID."""
    try:
        return await service.get_with_items(receipt_id=receipt_id)
    except DomainException as e:
        if e.code == ErrorCode.NOT_FOUND:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error getting receipt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting receipt: {str(e)}",
        )


@router.get(
    "/category/{category_id}/items", response_model=list[ReceiptItemsByCategory]
)
async def get_items_by_category(
    category_id: int,
    receipt_service: ReceiptServiceDep,
    category_service: CategoryServiceDep,
    skip: int = 0,
    limit: int = 100,
) -> list[ReceiptItemsByCategory]:
    """Get all receipt items in a category."""
    try:
        # Verify category exists
        category = await category_service.get(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        return await receipt_service.get_items_by_category(
            category_id=category_id, skip=skip, limit=limit
        )
    except DomainException as e:
        if e.code == ErrorCode.NOT_FOUND:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error getting items by category: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting items by category: {str(e)}",
        )

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.decorators import transactional
from app.core.exceptions import (
    ExternalAPIError,
    ImageProcessingError,
    ValidationError,
)
from app.integrations.gemini.receipt_analyzer import GeminiReceiptAnalyzer
from app.integrations.image_processing.image_processor import ImageProcessor
from app.models import (
    CategoryCreate,
    ReceiptCreate,
    ReceiptItemCreate,
    ReceiptRead,
    ReceiptUpdate,
)
from app.services.category import CategoryService
from app.services.receipt import ReceiptService

logger = logging.getLogger(__name__)


class ScannerService:
    """Service that orchestrates the receipt scanning process.

    This service is responsible for:
    1. Processing and analyzing receipt images
    2. Coordinating with other services to create database records
    3. Managing the complete receipt scanning workflow
    """

    # Class constants
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    DEFAULT_QUANTITY = 1.0
    CURRENCY_MAP = {
        "\u00a3": "£",  # Pound
        "\u20ac": "€",  # Euro
        "EUR": "€",
        "GBP": "£",
        "USD": "$",
    }

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service with required integrations."""
        self.session = session
        self.image_processor = ImageProcessor()
        self.receipt_analyzer = GeminiReceiptAnalyzer()

    # Public methods
    async def process_and_create_receipt(
        self,
        file: UploadFile,
        receipt_service: ReceiptService,
        category_service: CategoryService,
    ) -> ReceiptRead:
        """Process a receipt image and create all necessary database records.

        Args:
            file: The uploaded receipt image
            receipt_service: Service for receipt operations
            category_service: Service for category operations

        Returns:
            Complete receipt with items and categories

        Raises:
            ImageProcessingError: If image processing fails
            ValidationError: If receipt data is invalid
            ExternalAPIError: If AI analysis fails
        """
        # Save and analyze receipt
        file_path = settings.UPLOADS_ORIGINAL_DIR / file.filename
        await self._save_uploaded_file(file, file_path)

        # Get existing categories and analyze receipt
        existing_categories = await self._get_existing_categories(category_service)
        receipt_create, items_and_categories = await self.scan_and_analyze(
            str(file_path), existing_categories=existing_categories
        )

        # Create database records
        return await self._create_database_records(
            receipt_create,
            items_and_categories,
            receipt_service,
            category_service,
        )

    async def scan_and_analyze(
        self,
        image_path: str,
        existing_categories: list[dict] | None = None,
    ) -> tuple[ReceiptCreate, list[tuple[ReceiptItemCreate, CategoryCreate]]]:
        """Process and analyze a receipt image.

        Args:
            image_path: Path to the receipt image
            existing_categories: List of existing categories for better classification

        Returns:
            Tuple of receipt data and list of items with their categories

        Raises:
            ImageProcessingError: If image processing fails
            ExternalAPIError: If AI analysis fails
        """
        # Validate and process image
        processed_path, processed_image = await self._process_image(image_path)

        try:
            # Analyze receipt with AI
            raw_result = await self.receipt_analyzer.analyze_receipt(
                processed_image,
                existing_categories=existing_categories,
            )
            return self._process_raw_result(raw_result, str(processed_path))
        except Exception as e:
            if "Failed to read image" in str(e):
                raise ImageProcessingError(str(e))
            raise ExternalAPIError(f"Failed to analyze receipt: {str(e)}")

    # Core processing methods
    async def _process_image(self, image_path: str) -> tuple[Path, Any]:
        """Process the image and return the processed image path and data.

        Returns:
            Tuple of (processed image path, processed image data)

        Raises:
            ImageProcessingError: If image processing fails
        """
        # Validate image path
        original_path = Path(image_path)
        if not str(original_path).startswith(str(settings.UPLOADS_ORIGINAL_DIR)):
            raise ImageProcessingError(
                "Image must be in the uploads/original directory"
            )
        if not original_path.exists():
            raise ImageProcessingError(f"Image file not found: {image_path}")

        # Generate processed image path
        processed_filename = f"processed_{original_path.name}"
        processed_path = settings.UPLOADS_PROCESSED_DIR / processed_filename

        # Process image - let ImageProcessingError propagate up
        processed_image = self.image_processor.preprocess_image(str(original_path))
        self.image_processor.save_processed_image(processed_image, str(processed_path))
        return processed_path, processed_image

    def _process_raw_result(
        self,
        result: dict[str, Any],
        image_path: str,
    ) -> tuple[ReceiptCreate, list[tuple[ReceiptItemCreate, CategoryCreate]]]:
        """Process the raw JSON result from Gemini into structured data."""
        try:
            # Validate required fields
            required_fields = {"store_name", "total_amount", "currency", "items"}
            if not all(field in result for field in required_fields):
                raise ValidationError(
                    {"analysis": "Missing required fields in analysis result"}
                )

            # Process receipt data
            receipt = self._create_receipt_data(result, image_path)

            # Process items and their categories
            items_and_categories = self._create_items_and_categories(result["items"])

            return receipt, items_and_categories
        except (KeyError, TypeError, AttributeError) as e:
            raise ValidationError({"data": f"Invalid analysis result format: {str(e)}"})

    @transactional
    async def _create_database_records(
        self,
        receipt_create: ReceiptCreate,
        items_and_categories: list[tuple[ReceiptItemCreate, CategoryCreate]],
        receipt_service: ReceiptService,
        category_service: CategoryService,
    ) -> ReceiptRead:
        """Create all necessary database records in a single transaction."""
        # Create or get categories and build mapping
        category_map = await self._create_categories(
            items_and_categories, category_service
        )

        # Create receipt
        receipt = await receipt_service.create(receipt_create)

        # Create receipt items
        items_in = self._prepare_receipt_items(
            items_and_categories, category_map, receipt.id
        )
        if items_in:
            await receipt_service.create_items(items_in)

        # Mark receipt as processed
        await receipt_service.update(receipt.id, ReceiptUpdate(processed=True))

        # Return complete receipt
        return await receipt_service.get(receipt.id)

    # Data processing helpers
    def _create_receipt_data(
        self, result: dict[str, Any], image_path: str
    ) -> ReceiptCreate:
        """Create receipt data from raw result."""
        receipt_date = None
        if "date" in result:
            try:
                receipt_date = datetime.strptime(result["date"], self.DATETIME_FORMAT)
            except ValueError:
                logger.warning("Invalid date format in receipt, skipping date")

        return ReceiptCreate(
            store_name=result["store_name"],
            total_amount=result["total_amount"],
            currency=self._normalize_currency(result["currency"]),
            image_path=image_path,
            date=receipt_date,
        )

    def _create_items_and_categories(
        self, items: list[dict[str, Any]]
    ) -> list[tuple[ReceiptItemCreate, CategoryCreate]]:
        """Create items and categories from raw items data."""
        items_and_categories = []
        for item in items:
            category_info = item["category"]
            category = CategoryCreate(
                name=category_info["name"].strip().title(),
                description=category_info["description"].strip().capitalize(),
            )

            item_create = ReceiptItemCreate(
                name=item["name"],
                price=item["price"],
                quantity=item.get("quantity", self.DEFAULT_QUANTITY),
                currency=self._normalize_currency(item["currency"]),
            )
            items_and_categories.append((item_create, category))

        return items_and_categories

    # Database helpers
    @staticmethod
    async def _create_categories(
        items_and_categories: list[tuple[ReceiptItemCreate, CategoryCreate]],
        category_service: CategoryService,
    ) -> dict[str, int]:
        """Create or get categories and return name->id mapping."""
        category_map = {}
        for _, category_create in items_and_categories:
            if category_create.name not in category_map:
                category = await category_service.get_by_name(category_create.name)
                if not category:
                    category = await category_service.create(category_create)
                category_map[category_create.name] = category.id
        return category_map

    @staticmethod
    async def _get_existing_categories(
        category_service: CategoryService,
    ) -> list[dict[str, str]]:
        """Get existing categories for better classification."""
        categories = await category_service.list()
        return [
            {"name": cat.name, "description": cat.description} for cat in categories
        ]

    @staticmethod
    def _prepare_receipt_items(
        items_and_categories: list[tuple[ReceiptItemCreate, CategoryCreate]],
        category_map: dict[str, int],
        receipt_id: int,
    ) -> list[ReceiptItemCreate]:
        """Prepare receipt items with category IDs."""
        return [
            ReceiptItemCreate(
                name=item.name,
                price=item.price,
                quantity=item.quantity,
                currency=item.currency,
                category_id=category_map[category.name],
                receipt_id=receipt_id,
            )
            for item, category in items_and_categories
        ]

    # Utility methods
    @staticmethod
    async def _save_uploaded_file(
        file: UploadFile,
        file_path: Path,
    ) -> None:
        """Save uploaded file to disk."""
        try:
            with file_path.open("wb") as buffer:
                content = await file.read()
                buffer.write(content)
                await file.seek(0)
        except Exception as e:
            raise ImageProcessingError(f"Failed to save uploaded file: {str(e)}")

    def _normalize_currency(self, currency: str) -> str:
        """Normalize currency symbols to their proper representation."""
        return self.CURRENCY_MAP.get(currency, currency)

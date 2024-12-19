import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.exceptions import ExternalAPIError, ImageProcessingError, ValidationError
from app.integrations.gemini.receipt_analyzer import GeminiReceiptAnalyzer
from app.integrations.image_processing.image_processor import ImageProcessor
from app.models import AnalysisResult, ItemData, ReceiptData

logger = logging.getLogger(__name__)


class ReceiptScannerService:
    """Service that orchestrates the receipt scanning process."""

    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    DEFAULT_QUANTITY = 1.0

    def __init__(self):
        self.image_processor = ImageProcessor()
        self.receipt_analyzer = GeminiReceiptAnalyzer()

    @staticmethod
    def _normalize_currency(currency: str) -> str:
        """Normalize currency symbols to their proper representation."""
        currency_map = {
            "\u00a3": "£",  # Pound
            "\u20ac": "€",  # Euro
            "EUR": "€",
            "GBP": "£",
            "USD": "$",
        }
        return currency_map.get(currency, currency)

    def _process_raw_result(
        self, result: dict[str, Any], image_path: str
    ) -> AnalysisResult:
        """Process the raw JSON result from Gemini into structured data."""
        try:
            # Validate required fields
            required_fields = {"store_name", "total_amount", "currency", "items"}
            if not all(field in result for field in required_fields):
                raise ValidationError(
                    {"analysis": "Missing required fields in analysis result"}
                )

            # Process receipt data
            receipt_date = None
            if "date" in result:
                try:
                    receipt_date = datetime.strptime(
                        result["date"], self.DATETIME_FORMAT
                    )
                except ValueError:
                    logger.warning("Invalid date format in receipt, skipping date")

            receipt_data = ReceiptData(
                store_name=result["store_name"],
                total_amount=result["total_amount"],
                currency=self._normalize_currency(result["currency"]),
                image_path=image_path,
                date=receipt_date,
            )

            # Process items data
            items_data = []
            category_names = set()

            for item in result["items"]:
                category_info = item["category"]
                category_name = category_info["name"].strip().title()
                category_names.add(category_name)

                items_data.append(
                    ItemData(
                        name=item["name"],
                        price=item["price"],
                        quantity=item.get("quantity", self.DEFAULT_QUANTITY),
                        currency=self._normalize_currency(item["currency"]),
                        category_name=category_name,
                        category_description=category_info["description"]
                        .strip()
                        .capitalize(),
                    )
                )

            return AnalysisResult(
                receipt=receipt_data,
                items=items_data,
                category_names=list(category_names),
            )
        except (KeyError, TypeError, AttributeError) as e:
            raise ValidationError({"data": f"Invalid analysis result format: {str(e)}"})

    async def scan_and_analyze(
        self, image_path: str, existing_categories: list[dict] | None = None
    ) -> AnalysisResult:
        """Process and analyze a receipt image."""
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
        relative_processed_path = str(
            settings.UPLOADS_PROCESSED_DIR.relative_to(settings.UPLOAD_DIR.parent)
            / processed_filename
        )

        try:
            # Process image
            processed_image = self.image_processor.preprocess_image(str(original_path))
            self.image_processor.save_processed_image(
                processed_image, str(processed_path)
            )

            # Analyze receipt
            raw_result = await self.receipt_analyzer.analyze_receipt(
                processed_image,
                existing_categories=existing_categories,
            )
        except Exception as e:
            if "Failed to read image" in str(e):
                raise ImageProcessingError(str(e))
            raise ExternalAPIError(f"Failed to analyze receipt: {str(e)}")

        # Process results
        return self._process_raw_result(raw_result, str(relative_processed_path))

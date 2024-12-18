import logging
from pathlib import Path

from app.core.config import settings
from app.integrations.gemini.receipt_analyzer import (
    AnalysisResult,
    GeminiReceiptAnalyzer,
)
from app.integrations.image_processing.image_processor import ImageProcessor

logger = logging.getLogger(__name__)


class ReceiptScanner:
    """Integration layer component that orchestrates the receipt scanning process."""

    def __init__(self):
        self.image_processor = ImageProcessor()
        self.receipt_analyzer = GeminiReceiptAnalyzer()

    async def scan_and_analyze(
        self, image_path: str, existing_categories: list[dict] | None = None
    ) -> AnalysisResult:
        """Process and analyze a receipt image.

        Returns:
            AnalysisResult: A Pydantic model containing:
                - receipt: Receipt data (store name, total amount, etc.)
                - items: List of item data (name, price, quantity, category)
                - category_names: List of unique category names
        """
        try:
            # Validate image path and location
            original_path = Path(image_path)
            if not str(original_path).startswith(str(settings.UPLOADS_ORIGINAL_DIR)):
                raise ValueError("Image must be in the uploads/original directory")
            if not original_path.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            if not original_path.is_file():
                raise ValueError(f"Not a file: {image_path}")

            # Generate processed image path
            processed_filename = f"processed_{original_path.name}"
            processed_path = settings.UPLOADS_PROCESSED_DIR / processed_filename
            relative_processed_path = str(
                settings.UPLOADS_PROCESSED_DIR.relative_to(settings.UPLOAD_DIR.parent)
                / processed_filename
            )

            # Process and validate image
            processed_image = self.image_processor.preprocess_image(str(original_path))
            # Image validation is now done inside preprocess_image

            # Save processed image
            self.image_processor.save_processed_image(
                processed_image, str(processed_path)
            )

            # Analyze the processed image using Gemini
            return await self.receipt_analyzer.analyze_receipt(
                processed_image,
                str(relative_processed_path),
                existing_categories=existing_categories,
            )

        except Exception as e:
            logger.error(f"Error during receipt scanning: {str(e)}")
            raise

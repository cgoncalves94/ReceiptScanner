import logging
from pathlib import Path

from app.integrations.gemini.receipt_analyzer import GeminiReceiptAnalyzer
from app.integrations.image_processing.scanner import ImageProcessor
from app.schemas.receipt import ReceiptCreate

logger = logging.getLogger(__name__)


class ReceiptScanner:
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.receipt_analyzer = GeminiReceiptAnalyzer()

    async def scan_and_analyze(
        self, image_path: str
    ) -> tuple[ReceiptCreate, list[dict], list[str]]:
        """Process and analyze a receipt image."""
        try:
            # Preprocess the image to enhance readability
            processed_image = self.image_processor.preprocess_image(image_path)

            # Save processed image for record keeping
            processed_path = (
                Path(image_path).parent / f"processed_{Path(image_path).name}"
            )
            self.image_processor.save_processed_image(
                processed_image, str(processed_path)
            )

            # Analyze the enhanced image using Gemini
            return await self.receipt_analyzer.analyze_receipt(processed_image)

        except Exception as e:
            logger.error(f"Error during receipt scanning: {str(e)}")
            raise

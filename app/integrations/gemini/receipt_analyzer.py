import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TypeAlias

import google.generativeai as genai
from PIL import Image

from app.core.config import settings
from app.schemas import ReceiptCreate
from app.templates.prompts import RECEIPT_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)

# Type aliases
ReceiptAnalysis: TypeAlias = tuple[ReceiptCreate, list[dict], list[str]]
ItemData: TypeAlias = dict[str, str | float]


class GeminiReceiptAnalyzer:
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    DEFAULT_QUANTITY = 1.0
    MEMORY_IMAGE_PATH = "memory_image.jpg"

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured")

        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")

    @staticmethod
    def _normalize_category_name(name: str) -> str:
        """Normalize category names to avoid duplicates."""
        if not name:
            raise ValueError("Category name cannot be empty")
        return " ".join(name.lower().strip().split())

    @staticmethod
    def _validate_image(image: Image.Image) -> None:
        """Validate image format and dimensions."""
        if not isinstance(image, Image.Image):
            raise ValueError("Invalid image format")

        # Add any specific image validation requirements
        min_width, min_height = 100, 100  # Example minimum dimensions
        if image.width < min_width or image.height < min_height:
            raise ValueError(
                f"Image dimensions too small: {image.width}x{image.height}"
            )

    def _process_image_input(
        self, image_input: str | Image.Image
    ) -> tuple[Image.Image, str]:
        """Process and validate image input."""
        if isinstance(image_input, str):
            logger.info(f"Opening image from path: {image_input}")
            path = Path(image_input)
            if not path.exists():
                raise FileNotFoundError(f"Image file not found: {image_input}")
            if not path.is_file():
                raise ValueError(f"Not a file: {image_input}")

            image = Image.open(image_input)
            image_path = image_input
        else:
            logger.info("Using provided PIL Image")
            image = image_input
            image_path = self.MEMORY_IMAGE_PATH

        self._validate_image(image)
        return image, image_path

    async def analyze_receipt(self, image_input: str | Image.Image) -> ReceiptAnalysis:
        """Analyze receipt image using Gemini Vision API."""
        # Initialize image_path with a default value
        image_path = self.MEMORY_IMAGE_PATH

        try:
            image, image_path = self._process_image_input(image_input)
            logger.info("Successfully prepared image for analysis")

            response = self.model.generate_content([RECEIPT_ANALYSIS_PROMPT, image])
            response.resolve()

            if not response.text:
                raise ValueError("Empty response from Gemini API")

            logger.debug(f"Raw response from Gemini: {response.text}")

            result = json.loads(self._clean_response_text(response.text))
            self._validate_result(result)

            receipt = self._create_receipt(result, image_path)
            items_data, category_names = self._extract_items_and_categories(
                result["items"]
            )

            return receipt, items_data, category_names

        except Exception as e:
            logger.error(f"Error during receipt analysis: {str(e)}", exc_info=True)
            return self._create_fallback_response(image_path)

    @staticmethod
    def _validate_result(result: dict) -> None:
        """Validate the parsed JSON result has required fields."""
        required_fields = {"store_name", "total_amount", "items"}
        missing_fields = required_fields - set(result.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

    @staticmethod
    def _create_fallback_response(image_path: str) -> ReceiptAnalysis:
        """Create a fallback response when analysis fails."""
        return (
            ReceiptCreate(
                store_name="Unknown Store",
                total_amount=0.0,
                image_path=image_path,
                date=datetime.now(),  # Use current time as fallback
            ),
            [],
            [],
        )

    @staticmethod
    def _clean_response_text(text: str) -> str:
        """Clean the response text to ensure valid JSON."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    @staticmethod
    def _create_receipt(result: dict, image_path: str) -> ReceiptCreate:
        """Create a ReceiptCreate instance from the analysis result."""
        receipt_date = None
        if "date" in result:
            try:
                receipt_date = datetime.strptime(result["date"], "%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                logger.error(f"Error parsing date: {e}")

        return ReceiptCreate(
            store_name=result["store_name"],
            total_amount=result["total_amount"],
            image_path=image_path,
            date=receipt_date,
        )

    def _extract_items_and_categories(
        self, items: list[dict]
    ) -> tuple[list[dict], list[str]]:
        """Extract items data and category names from the analysis result."""
        categories_info = {}  # Store category info including descriptions
        items_data = []

        for item in items:
            category_info = item["category"]
            category_name = self._normalize_category_name(category_info["name"])

            if category_name not in categories_info:
                categories_info[category_name] = category_info["description"]

            items_data.append(
                {
                    "name": item["name"],
                    "price": item["price"],
                    "quantity": item.get("quantity", 1.0),
                    "category_name": category_name,
                    "category_description": category_info["description"],
                }
            )

        return items_data, list(categories_info.keys())

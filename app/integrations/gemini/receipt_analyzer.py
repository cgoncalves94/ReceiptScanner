import json
import logging
from datetime import datetime
from pathlib import Path

import google.generativeai as genai
from PIL import Image

from app.core.config import settings
from app.core.exceptions import DomainException, ErrorCode
from app.integrations.gemini.prompts import RECEIPT_ANALYSIS_PROMPT
from app.integrations.gemini.schemas import AnalysisResult, ItemData, ReceiptData

logger = logging.getLogger(__name__)


class GeminiReceiptAnalyzer:
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    DEFAULT_QUANTITY = 1.0

    def __init__(self):
        # Validate API key before initializing
        settings.validate_api_keys()

        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")

    @staticmethod
    def _build_prompt(existing_categories: list[dict] | None = None) -> str:
        """Build the prompt with existing categories if available."""
        prompt = RECEIPT_ANALYSIS_PROMPT

        if existing_categories:
            categories_info = "\n".join(
                [
                    f"- {cat['name']}: {cat['description']}"
                    for cat in existing_categories
                ]
            )

            prompt += f"""

Current Existing Categories:
{categories_info}

Note: Always try to use these existing categories first. Only create a new category if an item absolutely cannot fit into any of the categories above."""

        return prompt

    @staticmethod
    def _normalize_category_name(name: str) -> str:
        """Normalize category names to avoid duplicates and ensure proper capitalization."""
        if not name:
            raise ValueError("Category name cannot be empty")
        # Split, clean, and capitalize each word
        words = [word.strip().capitalize() for word in name.lower().split()]
        # Replace '&' with proper spacing
        name = " ".join(words).replace(" And ", " & ")
        return name

    @staticmethod
    def _normalize_category_description(description: str) -> str:
        """Normalize category descriptions to ensure proper capitalization."""
        if not description:
            raise ValueError("Category description cannot be empty")
        # Capitalize first letter, keep the rest as is for readability
        return description[0].upper() + description[1:]

    @staticmethod
    def _process_image_input(image_path: str) -> Image.Image:
        """Process and validate image input."""
        logger.info(f"Opening image from path: {image_path}")
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        if not path.is_file():
            raise ValueError(f"Not a file: {image_path}")

        return Image.open(image_path)

    async def analyze_receipt(
        self,
        image: Image.Image,
        image_path: str,
        existing_categories: list[dict] | None = None,
    ) -> AnalysisResult:
        """Analyze receipt image using Gemini Vision API."""
        try:
            prompt = self._build_prompt(existing_categories)
            response = self.model.generate_content([prompt, image])
            response.resolve()

            if not response.text:
                raise DomainException(
                    ErrorCode.VALIDATION_ERROR, "Empty response from Gemini API"
                )

            try:
                result = json.loads(self._clean_response_text(response.text))
            except json.JSONDecodeError as e:
                raise DomainException(
                    ErrorCode.VALIDATION_ERROR,
                    f"Failed to parse Gemini API response: {str(e)}",
                )

            self._validate_result(result)

            receipt_data = self._create_receipt_data(result, image_path)
            items_data, category_names = self._extract_items_and_categories(
                result["items"]
            )

            return AnalysisResult(
                receipt=receipt_data, items=items_data, category_names=category_names
            )

        except DomainException:
            raise
        except Exception as e:
            logger.error(f"Error during receipt analysis: {str(e)}", exc_info=True)
            raise DomainException(
                ErrorCode.INTERNAL_ERROR, f"Failed to analyze receipt: {str(e)}"
            )

    @staticmethod
    def _validate_result(result: dict) -> None:
        """Validate the parsed JSON result has required fields."""
        required_fields = {"store_name", "total_amount", "currency", "items"}
        missing_fields = required_fields - set(result.keys())
        if missing_fields:
            raise DomainException(
                ErrorCode.VALIDATION_ERROR,
                f"Missing required fields in analysis result: {missing_fields}",
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
    def _normalize_currency(currency: str) -> str:
        """Normalize currency symbols to their proper representation."""
        # Map of Unicode and other representations to standard symbols
        currency_map = {
            "\u00a3": "£",  # Pound
            "\u20ac": "€",  # Euro
            "EUR": "€",
            "GBP": "£",
            "USD": "$",
        }
        return currency_map.get(currency, currency)

    @staticmethod
    def _create_receipt_data(result: dict, image_path: str) -> ReceiptData:
        """Create receipt data from the analysis result."""
        receipt_date = None
        if "date" in result:
            try:
                receipt_date = datetime.strptime(result["date"], "%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                logger.error(f"Error parsing date: {e}")

        return ReceiptData(
            store_name=result["store_name"],
            total_amount=result["total_amount"],
            currency=GeminiReceiptAnalyzer._normalize_currency(result["currency"]),
            image_path=image_path,
            date=receipt_date,
        )

    def _extract_items_and_categories(
        self, items: list[dict]
    ) -> tuple[list[ItemData], list[str]]:
        """Extract items data and category names from the analysis result."""
        categories_info = {}  # Store category info including descriptions
        items_data = []

        for item in items:
            category_info = item["category"]
            category_name = self._normalize_category_name(category_info["name"])
            category_description = self._normalize_category_description(
                category_info["description"]
            )

            if category_name not in categories_info:
                categories_info[category_name] = category_description

            items_data.append(
                ItemData(
                    name=item["name"],
                    price=item["price"],
                    quantity=item.get("quantity", 1.0),
                    currency=self._normalize_currency(item["currency"]),
                    category_name=category_name,
                    category_description=category_description,
                )
            )

        return items_data, list(categories_info.keys())

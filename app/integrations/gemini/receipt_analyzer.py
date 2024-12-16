import json
import logging
from datetime import datetime
from pathlib import Path

import google.generativeai as genai
from PIL import Image

from app.core.config import settings
from app.schemas.receipt import ReceiptCreate

logger = logging.getLogger(__name__)


class GeminiReceiptAnalyzer:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")

    @staticmethod
    def _normalize_category_name(name: str) -> str:
        """Normalize category names to avoid duplicates by converting to lowercase and removing extra spaces."""
        return " ".join(name.lower().strip().split())

    async def analyze_receipt(
        self, image_input: str | Image.Image
    ) -> tuple[ReceiptCreate, list[dict], list[str]]:
        """
        Analyze receipt image using Gemini Vision API.
        Args:
            image_input: Either a path to an image file or a PIL Image object
        """
        try:
            # Handle image input
            if isinstance(image_input, str):
                logger.info(f"Opening image from path: {image_input}")
                if not Path(image_input).exists():
                    raise FileNotFoundError(f"Image file not found: {image_input}")
                image = Image.open(image_input)
                image_path = image_input
            else:
                logger.info("Using provided PIL Image")
                image = image_input
                image_path = "memory_image.jpg"  # Placeholder path for ReceiptCreate

            logger.info("Successfully prepared image for analysis")

            prompt = """
            You are a receipt analyzer. Your task is to extract information from a receipt image and return it in a specific JSON format.
            The response must be ONLY a valid JSON object with no additional text or markdown.

            Required format:
            {
                "store_name": "store name",
                "total_amount": float,
                "date": "YYYY-MM-DD HH:mm:ss",  # Extract the actual receipt date and time
                "items": [
                    {
                        "name": "item name",
                        "price": float,
                        "quantity": float,
                        "category": {
                            "name": "category name",  # Create a meaningful category name based on the item type
                            "description": "category description"  # Provide a clear description of what belongs in this category
                        }
                    }
                ]
            }

            Important:
            - The date should be extracted from the receipt and formatted exactly as "YYYY-MM-DD HH:mm:ss"
            - If you see a date like "21 JUL 2022", convert it to "2022-07-21"
            - Include the time if present in the receipt
            - For each item, create a meaningful category based on its characteristics
            - Each category should have a clear description explaining what types of items belong in it
            - Similar items should be grouped into the same category
            - Be specific but not too granular with categories (e.g., "dairy" for milk, cheese, yogurt instead of separate categories)
            """

            logger.info("Sending request to Gemini API")
            response = self.model.generate_content([prompt, image])
            response.resolve()
            logger.info(f"Raw response from Gemini: {response.text}")

            # Clean and parse response
            response_text = self._clean_response_text(response.text)
            result = json.loads(response_text)

            # Create receipt and extract data
            receipt = self._create_receipt(result, image_path)
            items_data, category_names = self._extract_items_and_categories(
                result["items"]
            )

            return receipt, items_data, category_names

        except FileNotFoundError as e:
            logger.error(f"File not found error: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.error(f"Invalid JSON text: {response_text}")
            raise
        except Exception as e:
            logger.error(f"Error during receipt analysis: {str(e)}")
            # Fallback to empty data if parsing fails
            return (
                ReceiptCreate(
                    store_name="Unknown Store", total_amount=0.0, image_path=image_path
                ),
                [],
                [],
            )

    def _clean_response_text(self, text: str) -> str:
        """Clean the response text to ensure valid JSON."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def _create_receipt(self, result: dict, image_path: str) -> ReceiptCreate:
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

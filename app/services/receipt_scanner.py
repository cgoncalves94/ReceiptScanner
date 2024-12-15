import json
import logging
from datetime import datetime
from pathlib import Path

import cv2
import google.generativeai as genai
import numpy as np
from PIL import Image

from app.core.config import settings
from app.models.receipt import ReceiptCreate

logger = logging.getLogger(__name__)


class ReceiptScanner:
    # Predefined categories with descriptions
    CATEGORIES = {
        "Groceries": "Basic food items and pantry staples",
        "Beverages": "Drinks, sodas, and non-alcoholic beverages",
        "Alcohol": "Beer, wine, and spirits",
        "Snacks": "Chips, candies, and other snack foods",
        "Produce": "Fresh fruits and vegetables",
        "Dairy": "Milk, cheese, and other dairy products",
        "Meat": "Fresh and processed meats",
        "Bakery": "Bread, pastries, and baked goods",
        "Personal Care": "Hygiene and beauty products",
        "Household": "Cleaning supplies and home essentials",
    }

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # List available models
        for m in genai.list_models():
            if "vision" in m.name:
                logger.info(f"Available vision model: {m.name}")
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")

    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Preprocess the receipt image for better text detection."""
        try:
            # Read the image
            logger.info(f"Reading image from {image_path}")
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to read image from {image_path}")

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            # Denoise
            denoised = cv2.fastNlMeansDenoising(thresh)
            return denoised
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            raise

    def _normalize_category_name(self, name: str) -> str:
        """Normalize category names to avoid duplicates."""
        # Convert to lowercase and remove extra spaces
        normalized = " ".join(name.lower().split())

        # Common substitutions to unify similar categories
        substitutions = {
            "sweets & snacks": "snacks",
            "dairy & alternatives": "dairy",
            "eggs & dairy": "dairy",
            "fresh produce": "produce",
            "bakery products": "bakery",
            "confectionery": "snacks",
        }

        return substitutions.get(normalized, normalized)

    async def analyze_receipt(
        self, image_path: str
    ) -> tuple[ReceiptCreate, list[dict], list[str]]:
        """Analyze receipt image using Gemini Vision API."""
        try:
            logger.info(f"Opening image for analysis: {image_path}")
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")

            image = Image.open(image_path)
            logger.info("Successfully opened image")

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
                            "name": "category name",  # Create a meaningful category name
                            "description": "category description"  # Provide a clear description of what belongs in this category
                        }
                    }
                ]
            }

            Important:
            - The date should be extracted from the receipt and formatted exactly as "YYYY-MM-DD HH:mm:ss"
            - If you see a date like "21 JUL 2022", convert it to "2022-07-21"
            - Include the time if present in the receipt
            - Create meaningful categories based on the items
            - Provide clear and descriptive category descriptions
            - Group similar items into the same category
            """

            logger.info("Sending request to Gemini API")
            response = self.model.generate_content([prompt, image])
            response.resolve()
            logger.info(f"Raw response from Gemini: {response.text}")

            # Try to clean the response text to ensure it's valid JSON
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            logger.info(f"Cleaned response text: {response_text}")
            result = json.loads(response_text)

            # Parse the date from the result
            receipt_date = None
            if "date" in result:
                try:
                    receipt_date = datetime.strptime(
                        result["date"], "%Y-%m-%d %H:%M:%S"
                    )
                except ValueError as e:
                    logger.error(f"Error parsing date: {e}")
                    receipt_date = None

            receipt = ReceiptCreate(
                store_name=result["store_name"],
                total_amount=result["total_amount"],
                image_path=image_path,
                date=receipt_date,
            )

            # Extract categories and items
            categories_info = {}  # Store category info including descriptions
            for item in result["items"]:
                category_info = item["category"]
                # Normalize the category name
                category_name = self._normalize_category_name(category_info["name"])
                if category_name not in categories_info:
                    categories_info[category_name] = category_info["description"]

            # Create items with normalized category names
            items = [
                {
                    "name": item["name"],
                    "price": item["price"],
                    "quantity": item.get("quantity", 1.0),
                    "category_name": self._normalize_category_name(
                        item["category"]["name"]
                    ),
                    "category_description": item["category"]["description"],
                }
                for item in result["items"]
            ]

            # Get unique category names
            category_names = list(categories_info.keys())

            return receipt, items, category_names
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

    def save_processed_image(
        self, processed_image: np.ndarray, output_path: str
    ) -> str:
        """Save the processed image for record keeping."""
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(output_path, processed_image)
            return output_path
        except Exception as e:
            logger.error(f"Error saving processed image: {str(e)}")
            raise

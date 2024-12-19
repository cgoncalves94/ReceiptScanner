import json
import logging

import google.generativeai as genai
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.exceptions import ExternalAPIError
from app.integrations.gemini.prompts import RECEIPT_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)


class GeminiReceiptAnalyzer:
    """Handles receipt analysis using Google's Gemini Vision API.

    This integration is responsible only for:
    1. Configuring and managing the Gemini API client
    2. Making API calls with retry logic
    3. Basic response validation and cleaning
    4. Returning the raw JSON response
    """

    def __init__(self):
        """Initialize the Gemini API client."""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _call_gemini_api(self, prompt: str, image: Image.Image) -> str:
        """Make the API call to Gemini with retry logic."""
        try:
            response = await self.model.generate_content_async([prompt, image])
            await response.resolve()

            if not response.text:
                raise ExternalAPIError("Empty response from Gemini API")

            return response.text
        except Exception as e:
            logger.error(f"Gemini API call failed: {str(e)}")
            raise ExternalAPIError(f"Failed to analyze receipt: {str(e)}")

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
    def _build_analysis_prompt(existing_categories: list[dict] | None = None) -> str:
        """Build the analysis prompt with optional existing categories.

        Args:
            existing_categories: Optional list of existing categories to guide analysis

        Returns:
            str: Complete analysis prompt with category guidance if provided
        """
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

    async def analyze_receipt(
        self,
        image: Image.Image,
        existing_categories: list[dict] | None = None,
    ) -> dict:
        """Analyze a receipt image using Gemini Vision API.

        Args:
            image: The preprocessed receipt image to analyze
            existing_categories: Optional list of existing categories to guide analysis

        Returns:
            dict: Raw JSON response from Gemini API

        Raises:
            ExternalAPIError: If API call or response parsing fails
        """
        try:
            # Build prompt and call Gemini API
            prompt = self._build_analysis_prompt(existing_categories)
            response_text = await self._call_gemini_api(prompt, image)

            # Parse and validate response
            try:
                return json.loads(self._clean_response_text(response_text))
            except json.JSONDecodeError as e:
                raise ExternalAPIError(f"Failed to parse Gemini API response: {str(e)}")

        except ExternalAPIError:
            raise
        except Exception as e:
            logger.error(f"Error during receipt analysis: {str(e)}", exc_info=True)
            raise ExternalAPIError(f"Failed to analyze receipt: {str(e)}")

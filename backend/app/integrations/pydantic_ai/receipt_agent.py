import os
from dataclasses import dataclass
from functools import cache
from io import BytesIO

import httpx
from google.genai.types import ThinkingLevel
from PIL import Image
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import BinaryContent
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from pydantic_ai.models.instrumented import InstrumentationSettings
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.retries import AsyncTenacityTransport, RetryConfig, wait_retry_after
from tenacity import retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError
from app.integrations.pydantic_ai.receipt_prompt import RECEIPT_SYSTEM_PROMPT
from app.integrations.pydantic_ai.receipt_schema import CurrencyCode, ReceiptAnalysis

# Model configuration - use Gemini 3 Flash by default (faster + cheaper than Pro)
# Set GEMINI_MODEL env var to override (e.g., "gemini-3-pro-preview" for higher quality)
DEFAULT_MODEL = "gemini-3-flash-preview"

# Default model settings:
# - timeout: 120 seconds (increased from 60 to handle image processing + thinking)
# - thinking_level: LOW to minimize latency (receipt scanning is straightforward)
#   Per Google docs: LOW = "Minimizes latency and cost. Best for simple instruction
#   following, chat, or high-throughput applications"
# Note: GoogleModelSettings expects ThinkingConfigDict but ThinkingConfig works at runtime
DEFAULT_MODEL_SETTINGS = GoogleModelSettings(
    timeout=120,
    google_thinking_config={"thinking_level": ThinkingLevel.LOW},
)


def _create_retrying_http_client() -> httpx.AsyncClient:
    """Create an HTTP client with smart retry handling for transient errors.

    Handles HTTP 429 (rate limit), 502, 503, 504 (server errors) with
    exponential backoff and Retry-After header support.

    Per Google's troubleshooting docs, 504 DEADLINE_EXCEEDED errors should be
    retried as they're often transient.
    """

    def should_retry_status(response: httpx.Response) -> None:
        """Raise exceptions for retryable HTTP status codes."""
        if response.status_code in (429, 502, 503, 504):
            response.raise_for_status()  # This will raise HTTPStatusError

    transport = AsyncTenacityTransport(
        config=RetryConfig(
            # Retry on HTTP errors (from validate_response) and connection issues
            retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError)),
            # Smart waiting: respects Retry-After headers, falls back to exponential backoff
            wait=wait_retry_after(
                fallback_strategy=wait_exponential(multiplier=2, max=30),
                max_wait=120,
            ),
            # Stop after 3 attempts (1 initial + 2 retries)
            stop=stop_after_attempt(3),
            # Re-raise the last exception if all retries fail
            reraise=True,
        ),
        validate_response=should_retry_status,
    )
    return httpx.AsyncClient(transport=transport, timeout=120)


@dataclass
class ReceiptDependencies:
    """Dependencies for receipt analysis."""

    image_bytes: bytes
    existing_categories: list[dict[str, str]] | None = None


@cache
def get_receipt_agent() -> Agent[ReceiptDependencies, ReceiptAnalysis]:
    """Lazily create and cache the receipt analyzer agent.

    This prevents import-time errors when API keys aren't available
    (e.g., during test discovery or in environments without credentials).
    """
    model_name = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

    # Create HTTP client with retry logic for transient errors (429, 502, 503, 504)
    http_client = _create_retrying_http_client()

    # Configure Google provider with API key and retrying HTTP client
    google_provider = GoogleProvider(
        api_key=settings.GEMINI_API_KEY,
        http_client=http_client,
    )
    google_model = GoogleModel(model_name, provider=google_provider)

    # Instrumentation settings for fine-grained Logfire tracing
    instrumentation = InstrumentationSettings(
        include_content=True,
        include_binary_content=settings.ENVIRONMENT.lower() != "production",
        version=2,
    )

    # Create receipt analyzer agent
    agent: Agent[ReceiptDependencies, ReceiptAnalysis] = Agent(
        model=google_model,
        deps_type=ReceiptDependencies,
        output_type=ReceiptAnalysis,
        system_prompt=RECEIPT_SYSTEM_PROMPT,
        model_settings=DEFAULT_MODEL_SETTINGS,
        retries=3,
        instrument=instrumentation,
    )

    # Register dynamic system prompt
    @agent.system_prompt
    def existing_categories_prompt(ctx: RunContext[ReceiptDependencies]) -> str:
        """Add existing categories to the system prompt if available."""
        categories = ctx.deps.existing_categories

        if not categories:
            return ""

        categories_info = "\n".join(
            [f"- {cat['name']}: {cat['description']}" for cat in categories]
        )

        return f"""
Current Existing Categories:
{categories_info}

Note:
1. Always try to use these existing categories first. Only create a new category if an item absolutely cannot fit into any of the categories above.
2. When creating new categories, provide detailed and informative descriptions that explain what types of items belong in the category.
3. Include examples of common items in the description, similar to the existing categories shown above.
4. Avoid generic descriptions like "Description of what belongs in this category".
"""

    # Register output validator
    @agent.output_validator
    def validate_currencies(result: ReceiptAnalysis) -> ReceiptAnalysis:
        """Validate and standardize currencies to ISO codes in the receipt analysis."""
        result.currency = CurrencyCode.standardize(result.currency)

        for item in result.items:
            item.currency = CurrencyCode.standardize(item.currency)
            if item.currency != result.currency:
                item.currency = result.currency

        return result

    return agent


async def analyze_receipt(
    image: Image.Image,
    existing_categories: list[dict[str, str]] | None = None,
) -> ReceiptAnalysis:
    """Analyze a receipt image using Pydantic AI agent with Gemini Vision.

    Args:
        image: The receipt image to analyze
        existing_categories: Optional list of existing categories to guide analysis

    Returns:
        ReceiptAnalysis: Structured receipt data
    """
    try:
        # Convert PIL Image to bytes
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format="PNG")
        img_bytes = img_byte_arr.getvalue()

        # Create dependencies
        deps = ReceiptDependencies(
            image_bytes=img_bytes,
            existing_categories=existing_categories,
        )

        # Create message with image
        messages: list[str | BinaryContent] = [
            "Please analyze this receipt image and extract the required information.",
            BinaryContent(data=img_bytes, media_type="image/png"),
        ]

        # Get the agent (lazily initialized) and run
        agent = get_receipt_agent()
        result = await agent.run(messages, deps=deps)
        return result.output

    except Exception as e:
        raise ServiceUnavailableError(f"Error analyzing receipt: {str(e)}") from e

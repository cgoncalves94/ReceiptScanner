import os
from dataclasses import dataclass
from io import BytesIO

from PIL import Image
from pydantic_ai import Agent, ModelSettings, RunContext
from pydantic_ai.messages import BinaryContent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.instrumented import InstrumentationSettings
from pydantic_ai.providers.google import GoogleProvider

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError
from app.integrations.pydantic_ai.receipt_prompt import RECEIPT_SYSTEM_PROMPT
from app.integrations.pydantic_ai.receipt_schema import CurrencySymbol, ReceiptAnalysis

# Model configuration - use Gemini 3 Flash by default (faster + cheaper than Pro)
# Set GEMINI_MODEL env var to override (e.g., "gemini-3-pro-preview" for higher quality)
DEFAULT_MODEL = "gemini-3-flash-preview"
_model_name = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

# Configure Google provider with API key
_google_provider = GoogleProvider(api_key=settings.GEMINI_API_KEY)
_google_model = GoogleModel(_model_name, provider=_google_provider)

# Default model settings with timeout (60 seconds for receipt analysis)
DEFAULT_MODEL_SETTINGS = ModelSettings(timeout=60)

# Instrumentation settings for fine-grained Logfire tracing
# - include_content: Log prompts and completions (useful for debugging)
# - include_binary_content: Log image data (disable in prod if bandwidth is concern)
# - version: Use latest OpenTelemetry GenAI spec format
_instrumentation = InstrumentationSettings(
    include_content=True,
    include_binary_content=settings.ENVIRONMENT.lower() != "production",
    version=2,
)


@dataclass
class ReceiptDependencies:
    """Dependencies for receipt analysis."""

    image_bytes: bytes
    existing_categories: list[dict[str, str]] | None = None


# Create receipt analyzer agent with Gemini 3 (or configured model)
receipt_agent: Agent[ReceiptDependencies, ReceiptAnalysis] = Agent(
    model=_google_model,
    deps_type=ReceiptDependencies,
    output_type=ReceiptAnalysis,
    system_prompt=RECEIPT_SYSTEM_PROMPT,
    model_settings=DEFAULT_MODEL_SETTINGS,
    retries=3,
    instrument=_instrumentation,
)


@receipt_agent.system_prompt
def existing_categories_prompt(ctx: RunContext[ReceiptDependencies]) -> str:
    """Add existing categories to the system prompt if available.

    Args:
        ctx: The run context containing dependencies

    Returns:
        System prompt with existing categories
    """
    # Get existing categories from dependencies
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


@receipt_agent.output_validator
def validate_currencies(result: ReceiptAnalysis) -> ReceiptAnalysis:
    """Validate and standardize currencies in the receipt analysis.

    Args:
        result: The receipt analysis result

    Returns:
        Validated receipt analysis
    """
    # Standardize the main receipt currency
    result.currency = CurrencySymbol.standardize(result.currency)

    # Standardize each item's currency and ensure it matches the receipt currency
    for item in result.items:
        # Standardize the item currency
        item.currency = CurrencySymbol.standardize(item.currency)

        # Ensure all items use the same currency as the receipt
        if item.currency != result.currency:
            item.currency = result.currency

    return result


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
        image.save(img_byte_arr, format=image.format or "PNG")
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

        # Run the agent with dependencies
        result = await receipt_agent.run(messages, deps=deps)
        return result.output

    except Exception as e:
        raise ServiceUnavailableError(f"Error analyzing receipt: {str(e)}") from e

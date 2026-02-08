import os
from dataclasses import dataclass
from functools import cache
from io import BytesIO
from typing import Any

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
from app.integrations.pydantic_ai.receipt_reconcile_prompt import (
    RECEIPT_RECONCILE_SYSTEM_PROMPT,
)
from app.integrations.pydantic_ai.receipt_reconcile_schema import (
    ReceiptReconcileAnalysis,
)

# Model configuration - use Gemini 3 Flash by default (faster + cheaper than Pro)
DEFAULT_MODEL = "gemini-3-flash-preview"

DEFAULT_MODEL_SETTINGS = GoogleModelSettings(
    timeout=120,
    google_thinking_config={"thinking_level": ThinkingLevel.LOW},
)


def _create_retrying_http_client() -> httpx.AsyncClient:
    """Create an HTTP client with smart retry handling for transient errors."""

    def should_retry_status(response: httpx.Response) -> None:
        if response.status_code in (429, 502, 503, 504):
            response.raise_for_status()

    transport = AsyncTenacityTransport(
        config=RetryConfig(
            retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError)),
            wait=wait_retry_after(
                fallback_strategy=wait_exponential(multiplier=2, max=30),
                max_wait=120,
            ),
            stop=stop_after_attempt(3),
            reraise=True,
        ),
        validate_response=should_retry_status,
    )
    return httpx.AsyncClient(transport=transport, timeout=120)


@dataclass
class ReceiptReconcileDependencies:
    """Dependencies for receipt reconciliation."""

    image_bytes: bytes
    receipt_total: str
    items: list[dict[str, Any]]


@cache
def get_receipt_reconcile_agent() -> Agent[
    ReceiptReconcileDependencies, ReceiptReconcileAnalysis
]:
    """Lazily create and cache the receipt reconciliation agent."""
    model_name = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

    http_client = _create_retrying_http_client()
    google_provider = GoogleProvider(
        api_key=settings.GEMINI_API_KEY,
        http_client=http_client,
    )
    google_model = GoogleModel(model_name, provider=google_provider)

    instrumentation = InstrumentationSettings(
        include_content=True,
        include_binary_content=settings.ENVIRONMENT.lower() != "production",
        version=2,
    )

    agent: Agent[ReceiptReconcileDependencies, ReceiptReconcileAnalysis] = Agent(
        model=google_model,
        deps_type=ReceiptReconcileDependencies,
        output_type=ReceiptReconcileAnalysis,
        system_prompt=RECEIPT_RECONCILE_SYSTEM_PROMPT,
        model_settings=DEFAULT_MODEL_SETTINGS,
        retries=3,
        instrument=instrumentation,
    )

    @agent.system_prompt
    def receipt_context(ctx: RunContext[ReceiptReconcileDependencies]) -> str:
        items_info = "\n".join(
            [
                (
                    f"- id:{item['id']} name:{item['name']} "
                    f"qty:{item['quantity']} unit_price:{item['unit_price']} "
                    f"total:{item['total_price']} currency:{item['currency']}"
                )
                for item in ctx.deps.items
            ]
        )

        return f"""
Receipt total: {ctx.deps.receipt_total}
Items:
{items_info}
"""

    return agent


async def analyze_reconciliation(
    image: Image.Image,
    receipt_total: str,
    items: list[dict[str, Any]],
) -> ReceiptReconcileAnalysis:
    """Reconcile receipt items using Pydantic AI agent with Gemini Vision."""
    try:
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format="PNG")
        img_bytes = img_byte_arr.getvalue()

        deps = ReceiptReconcileDependencies(
            image_bytes=img_bytes,
            receipt_total=receipt_total,
            items=items,
        )

        messages: list[str | BinaryContent] = [
            "Reconcile by marking duplicate/noise items for removal only.",
            BinaryContent(data=img_bytes, media_type="image/png"),
        ]

        agent = get_receipt_reconcile_agent()
        result = await agent.run(messages, deps=deps)
        return result.output

    except Exception as e:
        raise ServiceUnavailableError(f"Error reconciling receipt: {str(e)}") from e

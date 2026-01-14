"""Integration tests for the receipt scan endpoint.

These tests verify the full flow from HTTP request to database persistence,
using Pydantic AI's TestModel to simulate the Gemini Vision API response.

References:
- https://ai.pydantic.dev/testing/
- https://ai.pydantic.dev/api/models/test/
"""

from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from pydantic_ai.models.test import TestModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.category.models import Category
from app.integrations.pydantic_ai.receipt_agent import get_receipt_agent


@pytest.mark.asyncio
async def test_scan_receipt_creates_receipt_and_items(
    test_client: TestClient,
    test_image: BytesIO,
    mock_receipt_analysis: dict,
    auth_headers: dict[str, str],
) -> None:
    """Test that scanning a receipt creates receipt and items in database.

    Uses Pydantic AI's TestModel to simulate the Gemini Vision API response,
    while testing the full HTTP → Service → Database flow.
    """
    # Arrange: Create test model with custom output
    test_model = TestModel(custom_output_args=mock_receipt_analysis)

    # Act: Make request with mocked AI model
    with get_receipt_agent().override(model=test_model):
        response = test_client.post(
            "/api/v1/receipts/scan",
            files={"image": ("receipt.png", test_image, "image/png")},
            headers=auth_headers,
        )

    # Assert: Response is correct
    assert response.status_code == 201
    data = response.json()

    assert data["store_name"] == "Test Grocery Store"
    assert float(data["total_amount"]) == pytest.approx(25.98)
    assert data["currency"] == "EUR"  # Symbol € is standardized to ISO code
    assert len(data["items"]) == 3

    # Verify items were created with correct data
    item_names = {item["name"] for item in data["items"]}
    assert item_names == {"Organic Milk", "Whole Wheat Bread", "Bananas"}

    # Verify categories were created
    for item in data["items"]:
        assert item["category_id"] is not None


@pytest.mark.asyncio
async def test_scan_receipt_uses_existing_categories(
    test_client: TestClient,
    test_session: AsyncSession,
    test_image: BytesIO,
    mock_receipt_analysis: dict,
    test_user: User,
    auth_headers: dict[str, str],
) -> None:
    """Test that scanning uses existing categories when available."""
    # Arrange: Create an existing category that matches one in the mock response
    assert test_user.id is not None
    existing_category = Category(
        name="Dairy",
        description="Existing dairy category",
        user_id=test_user.id,
    )
    test_session.add(existing_category)
    await test_session.commit()
    await test_session.refresh(existing_category)

    test_model = TestModel(custom_output_args=mock_receipt_analysis)

    # Act
    with get_receipt_agent().override(model=test_model):
        response = test_client.post(
            "/api/v1/receipts/scan",
            files={"image": ("receipt.png", test_image, "image/png")},
            headers=auth_headers,
        )

    # Assert
    assert response.status_code == 201
    data = response.json()

    # Find the dairy item and verify it uses the existing category
    dairy_item = next(item for item in data["items"] if item["name"] == "Organic Milk")
    assert dairy_item["category_id"] == existing_category.id


@pytest.mark.asyncio
async def test_scan_receipt_with_invalid_image(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Test that scanning with invalid file returns 400 Bad Request."""
    # Arrange: Create invalid file content
    invalid_file = BytesIO(b"not an image")

    # Act
    response = test_client.post(
        "/api/v1/receipts/scan",
        files={"image": ("receipt.txt", invalid_file, "text/plain")},
        headers=auth_headers,
    )

    # Assert: Should return 400 with helpful error message
    assert response.status_code == 400
    assert "Invalid image file" in response.json()["detail"]


@pytest.mark.asyncio
async def test_scan_receipt_ai_failure_returns_503(
    test_client: TestClient,
    test_image: BytesIO,
    auth_headers: dict[str, str],
) -> None:
    """Test that AI service failure returns 503 Service Unavailable."""
    # Arrange: Create a broken model that will fail validation
    # by providing invalid output args (missing required fields)
    broken_model = TestModel(custom_output_args={"invalid": "data"})

    # Act
    with get_receipt_agent().override(model=broken_model):
        response = test_client.post(
            "/api/v1/receipts/scan",
            files={"image": ("receipt.png", test_image, "image/png")},
            headers=auth_headers,
        )

    # Assert: Should return 503 (wrapped by ServiceUnavailableError)
    assert response.status_code == 503
    assert "detail" in response.json()

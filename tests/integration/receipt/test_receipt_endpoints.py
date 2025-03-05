"""Tests for the receipt API endpoints."""

import json
from collections.abc import AsyncGenerator
from decimal import Decimal
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.receipt.models import Receipt
from app.domains.receipt.repositories import ReceiptRepository


@pytest_asyncio.fixture
async def test_receipt(test_session: AsyncSession) -> AsyncGenerator[Receipt, None]:
    """Create a test receipt."""
    repository = ReceiptRepository(test_session)
    receipt = Receipt(
        store_name="Test Store",
        total_amount=Decimal("10.99"),
        currency="$",
        image_path="/path/to/image.jpg",
    )
    created_receipt = await repository.create(receipt)
    yield created_receipt


@pytest.mark.asyncio
async def test_create_receipt_from_scan(test_client: TestClient) -> None:
    """Test creating a receipt from a scanned image."""
    # Create a test image file
    image_path = Path("tests/data/test_receipt.jpg")
    image_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a valid test image
    img = Image.new("RGB", (100, 100), color="white")
    img.save(image_path)

    try:
        # Prepare the file upload
        files = {"image": ("test_receipt.jpg", image_path.open("rb"), "image/jpeg")}

        # Make the request
        response = test_client.post("/api/v1/receipts/scan", files=files)

        # Assert response
        assert response.status_code == 201
        data = response.json()
        assert data["store_name"] is not None
        assert data["total_amount"] is not None
    finally:
        # Clean up
        image_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_list_receipts(test_client: TestClient, test_receipt: Receipt) -> None:
    """Test listing receipts."""
    # Make the request
    response = test_client.get("/api/v1/receipts")

    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0].get("id") == test_receipt.id


@pytest.mark.asyncio
async def test_get_receipt(test_client: TestClient, test_receipt: Receipt) -> None:
    """Test getting a receipt by ID."""
    # Make the request
    response = test_client.get(f"/api/v1/receipts/{test_receipt.id}")

    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_receipt.id
    assert data["store_name"] == test_receipt.store_name


@pytest.mark.asyncio
async def test_update_receipt(test_client: TestClient, test_receipt: Receipt) -> None:
    """Test updating a receipt."""
    # Prepare update data
    update_data = {
        "store_name": "Updated Store",
        "total_amount": 20.99,
    }

    # Make the request
    response = test_client.patch(
        f"/api/v1/receipts/{test_receipt.id}",
        content=json.dumps(update_data),
    )

    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["store_name"] == update_data["store_name"]
    assert float(data["total_amount"]) == update_data["total_amount"]


@pytest.mark.asyncio
async def test_get_nonexistent_receipt(test_client: TestClient) -> None:
    """Test getting a receipt that doesn't exist."""
    # Make the request
    response = test_client.get("/api/v1/receipts/999999")

    # Assert response
    assert response.status_code == 404

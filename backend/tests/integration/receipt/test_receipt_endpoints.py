"""Tests for the receipt API endpoints."""

import json

import pytest
from fastapi.testclient import TestClient

from app.category.models import Category
from app.receipt.models import Receipt, ReceiptItem


@pytest.mark.asyncio
async def test_list_receipts(test_client: TestClient, test_receipt: Receipt) -> None:
    """Test listing receipts."""
    response = test_client.get("/api/v1/receipts")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0].get("id") == test_receipt.id


@pytest.mark.asyncio
async def test_get_receipt(test_client: TestClient, test_receipt: Receipt) -> None:
    """Test getting a receipt by ID."""
    response = test_client.get(f"/api/v1/receipts/{test_receipt.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_receipt.id
    assert data["store_name"] == test_receipt.store_name


@pytest.mark.asyncio
async def test_update_receipt(test_client: TestClient, test_receipt: Receipt) -> None:
    """Test updating a receipt."""
    update_data = {
        "store_name": "Updated Store",
        "total_amount": 20.99,
    }

    response = test_client.patch(
        f"/api/v1/receipts/{test_receipt.id}",
        content=json.dumps(update_data),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["store_name"] == update_data["store_name"]
    assert float(data["total_amount"]) == update_data["total_amount"]


@pytest.mark.asyncio
async def test_get_nonexistent_receipt(test_client: TestClient) -> None:
    """Test getting a receipt that doesn't exist."""
    response = test_client.get("/api/v1/receipts/999999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_items_by_category(
    test_client: TestClient,
    test_receipt_item: ReceiptItem,
    test_category: Category,
) -> None:
    """Test listing receipt items by category."""
    response = test_client.get(f"/api/v1/receipts/category/{test_category.id}/items")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["name"] == test_receipt_item.name
    assert data[0]["category_id"] == test_category.id


@pytest.mark.asyncio
async def test_get_receipt_includes_metadata_fields(
    test_client: TestClient, test_receipt: Receipt
) -> None:
    """Test that receipt response includes metadata fields."""
    response = test_client.get(f"/api/v1/receipts/{test_receipt.id}")

    assert response.status_code == 200
    data = response.json()
    # Metadata fields should be present (even if null/empty)
    assert "notes" in data
    assert "tags" in data
    assert "payment_method" in data
    assert "tax_amount" in data
    # Default values for new receipts
    assert data["tags"] == []


@pytest.mark.asyncio
async def test_update_receipt_metadata(
    test_client: TestClient, test_receipt: Receipt
) -> None:
    """Test updating a receipt with metadata fields."""
    update_data = {
        "notes": "Weekly grocery run",
        "tags": ["groceries", "weekly", "essential"],
        "payment_method": "credit_card",
        "tax_amount": 5.25,
    }

    response = test_client.patch(
        f"/api/v1/receipts/{test_receipt.id}",
        content=json.dumps(update_data),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["notes"] == "Weekly grocery run"
    assert data["tags"] == ["groceries", "weekly", "essential"]
    assert data["payment_method"] == "credit_card"
    assert float(data["tax_amount"]) == 5.25


@pytest.mark.asyncio
async def test_update_receipt_clear_metadata(
    test_client: TestClient, test_receipt: Receipt
) -> None:
    """Test clearing metadata fields by setting them to null."""
    # First, set some metadata
    test_client.patch(
        f"/api/v1/receipts/{test_receipt.id}",
        content=json.dumps({
            "notes": "Some notes",
            "tags": ["tag1"],
            "payment_method": "cash",
            "tax_amount": 10.00,
        }),
    )

    # Now clear them
    update_data = {
        "notes": None,
        "tags": [],
        "payment_method": None,
        "tax_amount": None,
    }

    response = test_client.patch(
        f"/api/v1/receipts/{test_receipt.id}",
        content=json.dumps(update_data),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["notes"] is None
    assert data["tags"] == []
    assert data["payment_method"] is None
    assert data["tax_amount"] is None

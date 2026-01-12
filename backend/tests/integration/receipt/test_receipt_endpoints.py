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


# Filter Tests


@pytest.mark.asyncio
async def test_list_receipts_with_search_filter(
    test_client: TestClient, test_receipt: Receipt
) -> None:
    """Test filtering receipts by search term."""
    # Search for partial store name (case-insensitive)
    store_partial = test_receipt.store_name[:4].lower()
    response = test_client.get(f"/api/v1/receipts?search={store_partial}")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(r["id"] == test_receipt.id for r in data)


@pytest.mark.asyncio
async def test_list_receipts_with_store_filter(
    test_client: TestClient, test_receipt: Receipt
) -> None:
    """Test filtering receipts by exact store name."""
    response = test_client.get(f"/api/v1/receipts?store={test_receipt.store_name}")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all(r["store_name"] == test_receipt.store_name for r in data)


@pytest.mark.asyncio
async def test_list_receipts_with_amount_filter(
    test_client: TestClient, test_receipt: Receipt
) -> None:
    """Test filtering receipts by amount range."""
    min_amount = float(test_receipt.total_amount) - 1
    max_amount = float(test_receipt.total_amount) + 1

    response = test_client.get(
        f"/api/v1/receipts?min_amount={min_amount}&max_amount={max_amount}"
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(r["id"] == test_receipt.id for r in data)


@pytest.mark.asyncio
async def test_list_receipts_search_no_results(test_client: TestClient) -> None:
    """Test search filter returns empty list for non-matching term."""
    response = test_client.get("/api/v1/receipts?search=nonexistentstore12345")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_list_receipts_with_category_filter(
    test_client: TestClient,
    test_receipt: Receipt,
    test_receipt_item: ReceiptItem,
    test_category: Category,
) -> None:
    """Test filtering receipts by category ID."""
    response = test_client.get(f"/api/v1/receipts?category_ids={test_category.id}")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Verify the receipt with the test item is in the results
    assert any(r["id"] == test_receipt.id for r in data)

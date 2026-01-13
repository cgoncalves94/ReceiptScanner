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


# Item CRUD Tests


@pytest.mark.asyncio
async def test_create_receipt_item(
    test_client: TestClient,
    test_receipt: Receipt,
    test_category: Category,
) -> None:
    """Test creating a receipt item."""
    original_total = float(test_receipt.total_amount)
    item_data = {
        "name": "New Item",
        "quantity": 2,
        "unit_price": 5.50,
        "currency": "$",
        "category_id": test_category.id,
    }

    response = test_client.post(
        f"/api/v1/receipts/{test_receipt.id}/items",
        content=json.dumps(item_data),
    )

    assert response.status_code == 201
    data = response.json()
    # Check the item was added
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "New Item"
    assert data["items"][0]["quantity"] == 2
    assert float(data["items"][0]["unit_price"]) == 5.50
    assert float(data["items"][0]["total_price"]) == 11.00  # 2 * 5.50
    assert data["items"][0]["category_id"] == test_category.id
    # Check the receipt total was updated (use approx due to floating point)
    expected_total = original_total + 11.00
    assert abs(float(data["total_amount"]) - expected_total) < 0.01


@pytest.mark.asyncio
async def test_create_receipt_item_nonexistent_receipt(
    test_client: TestClient,
) -> None:
    """Test creating an item on a receipt that doesn't exist."""
    item_data = {
        "name": "New Item",
        "quantity": 1,
        "unit_price": 5.00,
        "currency": "$",
    }

    response = test_client.post(
        "/api/v1/receipts/999999/items",
        content=json.dumps(item_data),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_receipt_item(
    test_client: TestClient,
    test_receipt: Receipt,
    test_category: Category,
) -> None:
    """Test deleting a receipt item.

    We first create an item via the API (which updates the total),
    then delete it and verify the total is adjusted back.
    """
    # Create an item first via API to ensure totals are correctly tracked
    item_data = {
        "name": "Item to Delete",
        "quantity": 1,
        "unit_price": 5.00,
        "currency": "$",
        "category_id": test_category.id,
    }
    create_response = test_client.post(
        f"/api/v1/receipts/{test_receipt.id}/items",
        content=json.dumps(item_data),
    )
    assert create_response.status_code == 201
    created_data = create_response.json()
    item_id = created_data["items"][0]["id"]
    total_after_create = float(created_data["total_amount"])

    # Now delete the item
    response = test_client.delete(f"/api/v1/receipts/{test_receipt.id}/items/{item_id}")

    assert response.status_code == 200
    data = response.json()
    # Check the item was removed
    assert len(data["items"]) == 0
    # Check the receipt total was updated (reduced by the item total)
    expected_total = total_after_create - 5.00
    assert abs(float(data["total_amount"]) - expected_total) < 0.01


@pytest.mark.asyncio
async def test_delete_receipt_item_nonexistent_item(
    test_client: TestClient,
    test_receipt: Receipt,
) -> None:
    """Test deleting an item that doesn't exist."""
    response = test_client.delete(f"/api/v1/receipts/{test_receipt.id}/items/999999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_receipt_item_nonexistent_receipt(
    test_client: TestClient,
) -> None:
    """Test deleting an item from a receipt that doesn't exist."""
    response = test_client.delete("/api/v1/receipts/999999/items/1")

    assert response.status_code == 404


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

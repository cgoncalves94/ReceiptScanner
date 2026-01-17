"""Tests for the receipt API endpoints."""

import json

import pytest
from fastapi.testclient import TestClient

from app.category.models import Category
from app.receipt.models import Receipt, ReceiptItem


@pytest.mark.asyncio
async def test_list_receipts(
    test_client: TestClient,
    test_receipt: Receipt,
    auth_headers: dict[str, str],
) -> None:
    """Test listing receipts."""
    response = test_client.get("/api/v1/receipts", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0].get("id") == test_receipt.id


@pytest.mark.asyncio
async def test_get_receipt(
    test_client: TestClient, test_receipt: Receipt, auth_headers: dict[str, str]
) -> None:
    """Test getting a receipt by ID."""
    response = test_client.get(
        f"/api/v1/receipts/{test_receipt.id}", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_receipt.id
    assert data["store_name"] == test_receipt.store_name


@pytest.mark.asyncio
async def test_update_receipt(
    test_client: TestClient, test_receipt: Receipt, auth_headers: dict[str, str]
) -> None:
    """Test updating a receipt."""
    update_data = {
        "store_name": "Updated Store",
        "total_amount": 20.99,
    }

    response = test_client.patch(
        f"/api/v1/receipts/{test_receipt.id}",
        content=json.dumps(update_data),
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["store_name"] == update_data["store_name"]
    assert float(data["total_amount"]) == update_data["total_amount"]


@pytest.mark.asyncio
async def test_get_nonexistent_receipt(
    test_client: TestClient, auth_headers: dict[str, str]
) -> None:
    """Test getting a receipt that doesn't exist."""
    response = test_client.get("/api/v1/receipts/999999", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_items_by_category(
    test_client: TestClient,
    test_receipt_item: ReceiptItem,
    test_category: Category,
    auth_headers: dict[str, str],
) -> None:
    """Test listing receipt items by category."""
    response = test_client.get(
        f"/api/v1/receipts/category/{test_category.id}/items", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["name"] == test_receipt_item.name
    assert data[0]["category_id"] == test_category.id


@pytest.mark.asyncio
async def test_get_receipt_includes_metadata_fields(
    test_client: TestClient, test_receipt: Receipt, auth_headers: dict[str, str]
) -> None:
    """Test that receipt response includes metadata fields."""
    response = test_client.get(
        f"/api/v1/receipts/{test_receipt.id}", headers=auth_headers
    )

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
    test_client: TestClient, test_receipt: Receipt, auth_headers: dict[str, str]
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
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["notes"] == "Weekly grocery run"
    assert data["tags"] == ["groceries", "weekly", "essential"]
    assert data["payment_method"] == "credit_card"
    assert float(data["tax_amount"]) == 5.25


@pytest.mark.asyncio
async def test_update_receipt_clear_metadata(
    test_client: TestClient, test_receipt: Receipt, auth_headers: dict[str, str]
) -> None:
    """Test clearing metadata fields by setting them to null."""
    # First, set some metadata
    setup_response = test_client.patch(
        f"/api/v1/receipts/{test_receipt.id}",
        content=json.dumps(
            {
                "notes": "Some notes",
                "tags": ["tag1"],
                "payment_method": "cash",
                "tax_amount": 10.00,
            }
        ),
        headers=auth_headers,
    )
    assert setup_response.status_code == 200

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
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["notes"] is None
    assert data["tags"] == []
    assert data["payment_method"] is None
    assert data["tax_amount"] is None


# Item CRUD Tests


@pytest.mark.asyncio
async def test_create_receipt_item(
    test_client: TestClient,
    test_receipt: Receipt,
    test_category: Category,
    auth_headers: dict[str, str],
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
        headers=auth_headers,
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
    auth_headers: dict[str, str],
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
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_receipt_item(
    test_client: TestClient,
    test_receipt: Receipt,
    test_category: Category,
    auth_headers: dict[str, str],
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
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    created_data = create_response.json()
    item_id = created_data["items"][0]["id"]
    total_after_create = float(created_data["total_amount"])

    # Now delete the item
    response = test_client.delete(
        f"/api/v1/receipts/{test_receipt.id}/items/{item_id}", headers=auth_headers
    )

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
    auth_headers: dict[str, str],
) -> None:
    """Test deleting an item that doesn't exist."""
    response = test_client.delete(
        f"/api/v1/receipts/{test_receipt.id}/items/999999", headers=auth_headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_receipt_item_nonexistent_receipt(
    test_client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Test deleting an item from a receipt that doesn't exist."""
    response = test_client.delete(
        "/api/v1/receipts/999999/items/1", headers=auth_headers
    )

    assert response.status_code == 404


# Filter Tests


@pytest.mark.asyncio
async def test_list_receipts_with_search_filter(
    test_client: TestClient, test_receipt: Receipt, auth_headers: dict[str, str]
) -> None:
    """Test filtering receipts by search term."""
    # Search for partial store name (case-insensitive)
    store_partial = test_receipt.store_name[:4].lower()
    response = test_client.get(
        f"/api/v1/receipts?search={store_partial}", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(r["id"] == test_receipt.id for r in data)


@pytest.mark.asyncio
async def test_list_receipts_with_store_filter(
    test_client: TestClient, test_receipt: Receipt, auth_headers: dict[str, str]
) -> None:
    """Test filtering receipts by exact store name."""
    response = test_client.get(
        f"/api/v1/receipts?store={test_receipt.store_name}", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all(r["store_name"] == test_receipt.store_name for r in data)


@pytest.mark.asyncio
async def test_list_receipts_with_amount_filter(
    test_client: TestClient, test_receipt: Receipt, auth_headers: dict[str, str]
) -> None:
    """Test filtering receipts by amount range."""
    min_amount = float(test_receipt.total_amount) - 1
    max_amount = float(test_receipt.total_amount) + 1

    response = test_client.get(
        f"/api/v1/receipts?min_amount={min_amount}&max_amount={max_amount}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(r["id"] == test_receipt.id for r in data)


@pytest.mark.asyncio
async def test_list_receipts_search_no_results(
    test_client: TestClient, auth_headers: dict[str, str]
) -> None:
    """Test search filter returns empty list for non-matching term."""
    response = test_client.get(
        "/api/v1/receipts?search=nonexistentstore12345", headers=auth_headers
    )

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
    auth_headers: dict[str, str],
) -> None:
    """Test filtering receipts by category ID."""
    response = test_client.get(
        f"/api/v1/receipts?category_ids={test_category.id}", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Verify the receipt with the test item is in the results
    assert any(r["id"] == test_receipt.id for r in data)


@pytest.mark.asyncio
async def test_list_stores(
    test_client: TestClient, test_receipt: Receipt, auth_headers: dict[str, str]
) -> None:
    """Test listing unique store names."""
    response = test_client.get("/api/v1/receipts/stores", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # The store names should be sorted
    assert data == sorted(data)
    # Our test receipt's store should be in the list
    assert test_receipt.store_name in data


# Export Tests


@pytest.mark.asyncio
async def test_export_receipts_basic(
    test_client: TestClient, test_receipt: Receipt, auth_headers: dict[str, str]
) -> None:
    """Test basic CSV export without filters."""
    response = test_client.get("/api/v1/receipts/export", headers=auth_headers)

    assert response.status_code == 200
    # Check content type
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    # Check Content-Disposition header with filename
    assert "attachment" in response.headers["content-disposition"]
    assert "receipts_export_" in response.headers["content-disposition"]
    assert ".csv" in response.headers["content-disposition"]
    # Check CSV content is not empty
    csv_content = response.content.decode("utf-8")
    assert len(csv_content) > 0
    # Check CSV has header row
    lines = csv_content.strip().split("\n")
    assert len(lines) >= 1  # At least header
    # Check required columns in header
    header = lines[0]
    assert "receipt_id" in header
    assert "store_name" in header
    assert "receipt_total" in header
    assert "item_name" in header
    assert "category_name" in header


@pytest.mark.asyncio
async def test_export_receipts_with_filters(
    test_client: TestClient, test_receipt: Receipt, auth_headers: dict[str, str]
) -> None:
    """Test CSV export with filter parameters."""
    # Export with store filter
    response = test_client.get(
        f"/api/v1/receipts/export?store={test_receipt.store_name}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    csv_content = response.content.decode("utf-8")
    # CSV should contain the store name
    assert test_receipt.store_name in csv_content


@pytest.mark.asyncio
async def test_export_receipts_requires_authentication(
    test_client: TestClient,
) -> None:
    """Test that export endpoint requires authentication."""
    response = test_client.get("/api/v1/receipts/export")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_export_receipts_csv_structure(
    test_client: TestClient,
    test_receipt: Receipt,
    test_receipt_item: ReceiptItem,
    auth_headers: dict[str, str],
) -> None:
    """Test that exported CSV has correct structure with receipt and item data."""
    response = test_client.get("/api/v1/receipts/export", headers=auth_headers)

    assert response.status_code == 200
    csv_content = response.content.decode("utf-8")
    lines = csv_content.strip().split("\n")

    # Parse CSV header
    header = lines[0].split(",")
    expected_columns = [
        "receipt_id",
        "receipt_date",
        "store_name",
        "receipt_total",
        "receipt_currency",
        "payment_method",
        "tax_amount",
        "item_id",
        "item_name",
        "item_quantity",
        "item_unit_price",
        "item_total_price",
        "item_currency",
        "category_name",
    ]

    for col in expected_columns:
        assert col in header

    # At least one data row (header + data)
    assert len(lines) >= 2


@pytest.mark.asyncio
async def test_export_receipts_with_amount_filter(
    test_client: TestClient, test_receipt: Receipt, auth_headers: dict[str, str]
) -> None:
    """Test export with amount range filters."""
    min_amount = float(test_receipt.total_amount) - 1
    max_amount = float(test_receipt.total_amount) + 1

    response = test_client.get(
        f"/api/v1/receipts/export?min_amount={min_amount}&max_amount={max_amount}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    csv_content = response.content.decode("utf-8")
    # CSV should have content
    assert len(csv_content) > 100  # More than just header

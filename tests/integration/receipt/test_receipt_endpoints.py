"""Tests for the receipt API endpoints."""

import json
from collections.abc import AsyncGenerator
from decimal import Decimal

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.category.models import Category
from app.category.services import CategoryService
from app.receipt.models import Receipt, ReceiptCreate, ReceiptItem
from app.receipt.services import ReceiptService


@pytest_asyncio.fixture
async def test_receipt(test_session: AsyncSession) -> AsyncGenerator[Receipt]:
    """Create a test receipt."""
    category_service = CategoryService(test_session)
    receipt_service = ReceiptService(test_session, category_service)
    receipt_create = ReceiptCreate(
        store_name="Test Store",
        total_amount=Decimal("10.99"),
        currency="$",
        image_path="/path/to/image.jpg",
    )
    created_receipt = await receipt_service.create(receipt_create)
    yield created_receipt


@pytest_asyncio.fixture
async def test_category(test_session: AsyncSession) -> AsyncGenerator[Category]:
    """Create a test category."""
    category = Category(name="Test Category", description="Test Description")
    test_session.add(category)
    await test_session.commit()
    yield category


@pytest_asyncio.fixture
async def test_receipt_item(
    test_session: AsyncSession, test_receipt: Receipt, test_category: Category
) -> AsyncGenerator[ReceiptItem]:
    """Create a test receipt item in a category."""
    item = ReceiptItem(
        name="Test Item",
        quantity=2,
        unit_price=Decimal("5.50"),
        total_price=Decimal("11.00"),
        currency="$",
        receipt_id=test_receipt.id,
        category_id=test_category.id,
    )
    test_session.add(item)
    await test_session.commit()
    yield item


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


@pytest.mark.asyncio
async def test_list_items_by_category(
    test_client: TestClient, test_receipt_item: ReceiptItem, test_category: Category
) -> None:
    """Test listing receipt items by category."""
    # Make the request
    response = test_client.get(f"/api/v1/receipts/category/{test_category.id}/items")

    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["name"] == test_receipt_item.name
    assert data[0]["category_id"] == test_category.id

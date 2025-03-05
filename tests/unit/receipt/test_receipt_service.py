"""Unit tests for the receipt domain."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.domains.category.services import CategoryService
from app.domains.receipt.models import (
    Receipt,
    ReceiptCreate,
    ReceiptItem,
    ReceiptUpdate,
)
from app.domains.receipt.services import ReceiptService


@pytest.fixture
def mock_receipt_repo() -> AsyncMock:
    """Create a mock receipt repository."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def mock_category_service() -> AsyncMock:
    """Create a mock category service."""
    mock = AsyncMock(spec=CategoryService)
    return mock


@pytest.fixture
def receipt_service(
    mock_receipt_repo: AsyncMock, mock_category_service: AsyncMock
) -> ReceiptService:
    """Create a ReceiptService with mock dependencies."""
    return ReceiptService(
        receipt_repository=mock_receipt_repo,
        category_service=mock_category_service,
    )


@pytest.mark.asyncio
async def test_create_receipt(
    receipt_service: ReceiptService, mock_receipt_repo: AsyncMock
) -> None:
    """Test creating a receipt."""
    # Arrange
    receipt_in = ReceiptCreate(
        store_name="Test Store",
        total_amount=Decimal("10.99"),
        currency="$",
        image_path="/path/to/image.jpg",
    )
    mock_receipt_repo.create.return_value = Receipt(
        id=1,
        store_name=receipt_in.store_name,
        total_amount=receipt_in.total_amount,
        currency=receipt_in.currency,
        image_path=receipt_in.image_path,
    )

    # Act
    created_receipt = await receipt_service.create(receipt_in)

    # Assert
    assert created_receipt.id == 1
    assert created_receipt.store_name == receipt_in.store_name
    assert created_receipt.total_amount == receipt_in.total_amount
    assert created_receipt.currency == receipt_in.currency
    assert created_receipt.image_path == receipt_in.image_path
    mock_receipt_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_get_receipt(
    receipt_service: ReceiptService, mock_receipt_repo: AsyncMock
) -> None:
    """Test getting a receipt by ID."""
    # Arrange
    receipt = Receipt(
        id=1,
        store_name="Test Store",
        total_amount=Decimal("10.99"),
        currency="$",
        image_path="/path/to/image.jpg",
    )
    mock_receipt_repo.get.return_value = receipt

    # Act
    retrieved_receipt = await receipt_service.get(receipt.id)

    # Assert
    assert retrieved_receipt.id == receipt.id
    assert retrieved_receipt.store_name == receipt.store_name
    assert retrieved_receipt.total_amount == receipt.total_amount
    mock_receipt_repo.get.assert_called_once_with(receipt.id)


@pytest.mark.asyncio
async def test_get_nonexistent_receipt(
    receipt_service: ReceiptService, mock_receipt_repo: AsyncMock
) -> None:
    """Test getting a receipt that doesn't exist."""
    # Arrange
    mock_receipt_repo.get.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await receipt_service.get(999)
    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_list_receipts(
    receipt_service: ReceiptService, mock_receipt_repo: AsyncMock
) -> None:
    """Test listing receipts."""
    # Arrange
    receipts = [
        Receipt(
            id=i,
            store_name=f"Store {i}",
            total_amount=Decimal(f"{10.99 + i}"),
            currency="$",
            image_path=f"/path/to/image{i}.jpg",
        )
        for i in range(1, 4)
    ]
    mock_receipt_repo.list.return_value = receipts[:2]  # Return only first 2

    # Act
    retrieved_receipts = await receipt_service.list(skip=0, limit=2)

    # Assert
    assert len(retrieved_receipts) == 2
    mock_receipt_repo.list.assert_called_once_with(skip=0, limit=2)


@pytest.mark.asyncio
async def test_update_receipt(
    receipt_service: ReceiptService, mock_receipt_repo: AsyncMock
) -> None:
    """Test updating a receipt."""
    # Arrange
    existing_receipt = Receipt(
        id=1,
        store_name="Old Store",
        total_amount=Decimal("10.99"),
        currency="$",
        image_path="/path/to/image.jpg",
    )
    mock_receipt_repo.get.return_value = existing_receipt

    update_data = ReceiptUpdate(
        store_name="New Store",
        total_amount=Decimal("20.99"),
    )

    mock_receipt_repo.update.return_value = Receipt(
        id=existing_receipt.id,
        store_name=update_data.store_name,
        total_amount=update_data.total_amount,
        currency=existing_receipt.currency,
        image_path=existing_receipt.image_path,
    )

    # Act
    updated_receipt = await receipt_service.update(existing_receipt.id, update_data)

    # Assert
    assert updated_receipt.store_name == update_data.store_name
    assert updated_receipt.total_amount == update_data.total_amount
    assert updated_receipt.id == existing_receipt.id
    mock_receipt_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_nonexistent_receipt(
    receipt_service: ReceiptService, mock_receipt_repo: AsyncMock
) -> None:
    """Test updating a receipt that doesn't exist."""
    # Arrange
    mock_receipt_repo.get.return_value = None
    update_data = ReceiptUpdate(
        store_name="New Store",
        total_amount=Decimal("20.99"),
    )

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await receipt_service.update(999, update_data)
    assert "not found" in str(exc_info.value)
    mock_receipt_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_delete_receipt(
    receipt_service: ReceiptService, mock_receipt_repo: AsyncMock
) -> None:
    """Test deleting a receipt."""
    # Arrange
    receipt = Receipt(
        id=1,
        store_name="Test Store",
        total_amount=Decimal("10.99"),
        currency="$",
        image_path="/path/to/image.jpg",
    )
    mock_receipt_repo.get.return_value = receipt

    # Act
    await receipt_service.delete(receipt.id)

    # Assert
    mock_receipt_repo.delete.assert_called_once_with(receipt)


@pytest.mark.asyncio
async def test_list_items_by_category(
    receipt_service: ReceiptService,
    mock_receipt_repo: AsyncMock,
    mock_category_service: AsyncMock,
) -> None:
    """Test listing receipt items by category."""
    # Arrange
    category_id = 1
    mock_category = MagicMock(id=category_id)
    mock_category_service.get.return_value = mock_category

    items = [
        ReceiptItem(
            id=i,
            name=f"Item {i}",
            quantity=1,
            unit_price=Decimal("10.99"),
            total_price=Decimal("10.99"),
            currency="$",
            category_id=category_id,
            receipt_id=1,
        )
        for i in range(1, 3)
    ]
    mock_receipt_repo.list_items_by_category.return_value = items

    # Act
    retrieved_items = await receipt_service.list_items_by_category(
        category_id=category_id
    )

    # Assert
    assert len(retrieved_items) == 2
    assert all(item.category_id == category_id for item in retrieved_items)
    mock_receipt_repo.list_items_by_category.assert_called_once_with(
        category_id=category_id, skip=0, limit=100
    )

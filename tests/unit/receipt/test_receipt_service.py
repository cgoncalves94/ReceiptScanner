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


def test_receipt_item_total_cost():
    """Test the total_cost computed property of ReceiptItem."""
    # Arrange
    item = ReceiptItem(
        name="Test Item",
        quantity=2,
        unit_price=Decimal("10.50"),
        total_price=Decimal("21.00"),
        currency="$",
        receipt_id=1,
    )

    # Act
    total_cost = item.total_cost

    # Assert
    assert total_cost == Decimal("21.00")
    assert total_cost == item.unit_price * item.quantity


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock database session."""
    mock = AsyncMock()
    # Configure add method to be a regular MagicMock, not a coroutine
    mock.add = MagicMock()
    return mock


@pytest.fixture
def mock_category_service() -> AsyncMock:
    """Create a mock category service."""
    mock = AsyncMock(spec=CategoryService)
    return mock


@pytest.fixture
def receipt_service(
    mock_session: AsyncMock, mock_category_service: AsyncMock
) -> ReceiptService:
    """Create a ReceiptService with mock dependencies."""
    return ReceiptService(
        session=mock_session,
        category_service=mock_category_service,
    )


@pytest.mark.asyncio
async def test_create_receipt(
    receipt_service: ReceiptService, mock_session: AsyncMock
) -> None:
    """Test creating a receipt."""
    # Arrange
    receipt_in = ReceiptCreate(
        store_name="Test Store",
        total_amount=Decimal("10.99"),
        currency="$",
        image_path="/path/to/image.jpg",
    )

    # Mock the flush method
    mock_session.flush = AsyncMock()

    # Act
    created_receipt = await receipt_service.create(receipt_in)

    # Assert
    assert created_receipt.store_name == receipt_in.store_name
    assert created_receipt.total_amount == receipt_in.total_amount
    assert created_receipt.currency == receipt_in.currency
    assert created_receipt.image_path == receipt_in.image_path
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_get_receipt(
    receipt_service: ReceiptService, mock_session: AsyncMock
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
    mock_session.scalar.return_value = receipt
    mock_session.refresh = AsyncMock()

    # Act
    retrieved_receipt = await receipt_service.get(receipt.id)

    # Assert
    assert retrieved_receipt.id == receipt.id
    assert retrieved_receipt.store_name == receipt.store_name
    assert retrieved_receipt.total_amount == receipt.total_amount
    mock_session.scalar.assert_called_once()
    mock_session.refresh.assert_called_once_with(receipt, ["items"])


@pytest.mark.asyncio
async def test_get_nonexistent_receipt(
    receipt_service: ReceiptService, mock_session: AsyncMock
) -> None:
    """Test getting a receipt that doesn't exist."""
    # Arrange
    mock_session.scalar.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await receipt_service.get(999)
    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_list_receipts(
    receipt_service: ReceiptService, mock_session: AsyncMock
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

    # Mock the session.scalars().all() chain
    mock_session.scalars = AsyncMock()
    # Make scalars() return an object with a non-coroutine all() method
    mock_session.scalars.return_value = MagicMock()
    mock_session.scalars.return_value.all.return_value = receipts[
        :2
    ]  # Return only first 2

    # Mock the refresh method
    mock_session.refresh = AsyncMock()

    # Act
    retrieved_receipts = await receipt_service.list(skip=0, limit=2)

    # Assert
    assert len(retrieved_receipts) == 2
    mock_session.scalars.assert_called_once()
    assert mock_session.refresh.call_count == 2  # Called once for each receipt


@pytest.mark.asyncio
async def test_update_receipt(
    receipt_service: ReceiptService, mock_session: AsyncMock
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

    # Mock the scalar method for get
    mock_session.scalar.return_value = existing_receipt

    # Mock the flush and refresh methods
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()

    update_data = ReceiptUpdate(
        store_name="New Store",
        total_amount=Decimal("20.99"),
    )

    # Act
    updated_receipt = await receipt_service.update(existing_receipt.id, update_data)

    # Assert
    assert updated_receipt.store_name == update_data.store_name
    assert updated_receipt.total_amount == update_data.total_amount
    assert updated_receipt.id == existing_receipt.id
    mock_session.scalar.assert_called_once()
    mock_session.flush.assert_called_once()
    assert mock_session.refresh.call_count == 2  # Called once in get and once in update


@pytest.mark.asyncio
async def test_update_nonexistent_receipt(
    receipt_service: ReceiptService, mock_session: AsyncMock
) -> None:
    """Test updating a receipt that doesn't exist."""
    # Arrange
    mock_session.scalar.return_value = None
    update_data = ReceiptUpdate(
        store_name="New Store",
        total_amount=Decimal("20.99"),
    )

    # Mock the flush method
    mock_session.flush = AsyncMock()

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await receipt_service.update(999, update_data)
    assert "not found" in str(exc_info.value)
    mock_session.flush.assert_not_called()


@pytest.mark.asyncio
async def test_delete_receipt(
    receipt_service: ReceiptService, mock_session: AsyncMock
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
    mock_session.scalar.return_value = receipt

    # Mock the delete and flush methods
    mock_session.delete = AsyncMock()
    mock_session.flush = AsyncMock()

    # Act
    await receipt_service.delete(receipt.id)

    # Assert
    mock_session.delete.assert_called_once_with(receipt)
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_list_items_by_category(
    receipt_service: ReceiptService,
    mock_session: AsyncMock,
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

    # Mock the session.scalars().all() chain
    mock_session.scalars = AsyncMock()
    # Make scalars() return an object with a non-coroutine all() method
    mock_session.scalars.return_value = MagicMock()
    mock_session.scalars.return_value.all.return_value = items

    # Act
    retrieved_items = await receipt_service.list_items_by_category(
        category_id=category_id
    )

    # Assert
    assert len(retrieved_items) == 2
    assert all(item.category_id == category_id for item in retrieved_items)
    mock_session.scalars.assert_called_once()

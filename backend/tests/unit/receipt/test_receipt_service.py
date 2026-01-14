"""Unit tests for the receipt domain."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.category.services import CategoryService
from app.core.exceptions import BadRequestError, NotFoundError
from app.receipt.models import (
    PaymentMethod,
    Receipt,
    ReceiptCreate,
    ReceiptItem,
    ReceiptItemCreateRequest,
    ReceiptItemUpdate,
    ReceiptUpdate,
)
from app.receipt.services import ReceiptService

# Test user ID for data isolation
TEST_USER_ID = 1


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
    created_receipt = await receipt_service.create(receipt_in, user_id=TEST_USER_ID)

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
    assert receipt.id is not None
    mock_session.scalar.return_value = receipt
    mock_session.refresh = AsyncMock()

    # Act
    retrieved_receipt = await receipt_service.get(receipt.id, user_id=TEST_USER_ID)

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
        await receipt_service.get(999, user_id=TEST_USER_ID)
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

    # Mock the session.exec().all() chain
    mock_session.exec = AsyncMock()
    # Make exec() return an object with a non-coroutine all() method
    mock_session.exec.return_value = MagicMock()
    mock_session.exec.return_value.all.return_value = receipts[
        :2
    ]  # Return only first 2

    # Act
    retrieved_receipts = await receipt_service.list(
        skip=0, limit=2, user_id=TEST_USER_ID
    )

    # Assert
    assert len(retrieved_receipts) == 2
    mock_session.exec.assert_called_once()
    # With selectinload, no refresh calls are needed (N+1 optimization)


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
    assert existing_receipt.id is not None

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
    updated_receipt = await receipt_service.update(
        existing_receipt.id, update_data, user_id=TEST_USER_ID
    )

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
        await receipt_service.update(999, update_data, user_id=TEST_USER_ID)
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
    assert receipt.id is not None
    mock_session.scalar.return_value = receipt

    # Mock the delete and flush methods
    mock_session.delete = AsyncMock()
    mock_session.flush = AsyncMock()

    # Act
    await receipt_service.delete(receipt.id, user_id=TEST_USER_ID)

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

    # Mock the session.exec().all() chain
    mock_session.exec = AsyncMock()
    # Make exec() return an object with a non-coroutine all() method
    mock_session.exec.return_value = MagicMock()
    mock_session.exec.return_value.all.return_value = items

    # Act
    retrieved_items = await receipt_service.list_items_by_category(
        category_id=category_id, user_id=TEST_USER_ID
    )

    # Assert
    assert len(retrieved_items) == 2
    assert all(item.category_id == category_id for item in retrieved_items)
    mock_session.exec.assert_called_once()


@pytest.mark.asyncio
async def test_update_receipt_item(
    receipt_service: ReceiptService, mock_session: AsyncMock
) -> None:
    """Test updating a receipt item."""
    # Arrange
    item = ReceiptItem(
        id=1,
        name="Original Item",
        quantity=1,
        unit_price=Decimal("10.99"),
        total_price=Decimal("10.99"),
        currency="$",
        category_id=1,
        receipt_id=1,
    )
    receipt = Receipt(
        id=1,
        store_name="Test Store",
        total_amount=Decimal("10.99"),
        currency="$",
        image_path="/path/to/image.jpg",
        items=[item],
    )
    mock_session.scalar.return_value = receipt
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()

    update_data = ReceiptItemUpdate(name="Updated Item", category_id=2)

    # Act
    updated_receipt = await receipt_service.update_item(
        receipt_id=1, item_id=1, item_in=update_data, user_id=TEST_USER_ID
    )

    # Assert
    assert updated_receipt.items[0].name == "Updated Item"
    assert updated_receipt.items[0].category_id == 2
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_update_nonexistent_receipt_item(
    receipt_service: ReceiptService, mock_session: AsyncMock
) -> None:
    """Test updating a receipt item that doesn't exist."""
    # Arrange
    receipt = Receipt(
        id=1,
        store_name="Test Store",
        total_amount=Decimal("10.99"),
        currency="$",
        image_path="/path/to/image.jpg",
        items=[],  # No items
    )
    mock_session.scalar.return_value = receipt
    mock_session.refresh = AsyncMock()

    update_data = ReceiptItemUpdate(name="Updated Item")

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await receipt_service.update_item(
            receipt_id=1, item_id=999, item_in=update_data, user_id=TEST_USER_ID
        )
    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_receipt_with_metadata(
    receipt_service: ReceiptService, mock_session: AsyncMock
) -> None:
    """Test updating a receipt with metadata fields (notes, tags, payment_method, tax_amount)."""
    # Arrange
    existing_receipt = Receipt(
        id=1,
        store_name="Test Store",
        total_amount=Decimal("100.00"),
        currency="$",
        image_path="/path/to/image.jpg",
        notes=None,
        payment_method=None,
        tax_amount=None,
        tags=[],
    )

    # Mock the scalar method for get
    mock_session.scalar.return_value = existing_receipt

    # Mock the flush and refresh methods
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()

    update_data = ReceiptUpdate(
        notes="Weekly grocery shopping",
        tags=["groceries", "weekly"],
        payment_method=PaymentMethod.CREDIT_CARD,
        tax_amount=Decimal("8.50"),
    )

    # Act
    updated_receipt = await receipt_service.update(
        existing_receipt.id, update_data, user_id=TEST_USER_ID
    )

    # Assert
    assert updated_receipt.notes == "Weekly grocery shopping"
    assert updated_receipt.tags == ["groceries", "weekly"]
    assert updated_receipt.payment_method == PaymentMethod.CREDIT_CARD
    assert updated_receipt.tax_amount == Decimal("8.50")
    mock_session.flush.assert_called_once()


def test_receipt_with_metadata_fields():
    """Test that Receipt model accepts metadata fields."""
    # Arrange & Act
    receipt = Receipt(
        id=1,
        store_name="Test Store",
        total_amount=Decimal("50.00"),
        currency="$",
        image_path="/path/to/image.jpg",
        notes="Some notes",
        payment_method=PaymentMethod.MOBILE_PAYMENT,
        tax_amount=Decimal("4.25"),
        tags=["quick", "lunch"],
    )

    # Assert
    assert receipt.notes == "Some notes"
    assert receipt.payment_method == PaymentMethod.MOBILE_PAYMENT
    assert receipt.tax_amount == Decimal("4.25")
    assert receipt.tags == ["quick", "lunch"]


def test_payment_method_enum_values():
    """Test that PaymentMethod enum has expected values."""
    assert PaymentMethod.CASH.value == "cash"
    assert PaymentMethod.CREDIT_CARD.value == "credit_card"
    assert PaymentMethod.DEBIT_CARD.value == "debit_card"
    assert PaymentMethod.MOBILE_PAYMENT.value == "mobile_payment"
    assert PaymentMethod.OTHER.value == "other"


# Item CRUD Tests


@pytest.mark.asyncio
async def test_create_item(
    receipt_service: ReceiptService, mock_session: AsyncMock
) -> None:
    """Test creating a receipt item and updating receipt total."""
    # Arrange
    receipt = Receipt(
        id=1,
        store_name="Test Store",
        total_amount=Decimal("10.00"),
        currency="$",
        image_path="/path/to/image.jpg",
        items=[],
    )
    mock_session.scalar.return_value = receipt
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()

    item_data = ReceiptItemCreateRequest(
        name="New Item",
        quantity=2,
        unit_price=Decimal("5.50"),
        currency="$",
        category_id=1,
    )

    # Act
    updated_receipt = await receipt_service.create_item(
        receipt_id=1, item_in=item_data, user_id=TEST_USER_ID
    )

    # Assert
    # Total should be original (10.00) + new item total (2 * 5.50 = 11.00) = 21.00
    assert updated_receipt.total_amount == Decimal("21.00")
    mock_session.add.assert_called()
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_create_item_nonexistent_receipt(
    receipt_service: ReceiptService, mock_session: AsyncMock
) -> None:
    """Test creating an item on a receipt that doesn't exist."""
    # Arrange
    mock_session.scalar.return_value = None

    item_data = ReceiptItemCreateRequest(
        name="New Item",
        quantity=1,
        unit_price=Decimal("5.00"),
        currency="$",
    )

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await receipt_service.create_item(
            receipt_id=999, item_in=item_data, user_id=TEST_USER_ID
        )
    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_item(
    receipt_service: ReceiptService, mock_session: AsyncMock
) -> None:
    """Test deleting a receipt item and updating receipt total."""
    # Arrange
    item = ReceiptItem(
        id=1,
        name="Item to Delete",
        quantity=1,
        unit_price=Decimal("5.00"),
        total_price=Decimal("5.00"),
        currency="$",
        receipt_id=1,
    )
    receipt = Receipt(
        id=1,
        store_name="Test Store",
        total_amount=Decimal("15.00"),
        currency="$",
        image_path="/path/to/image.jpg",
        items=[item],
    )
    mock_session.scalar.return_value = receipt
    mock_session.delete = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()

    # Act
    updated_receipt = await receipt_service.delete_item(
        receipt_id=1, item_id=1, user_id=TEST_USER_ID
    )

    # Assert
    # Total should be original (15.00) - deleted item (5.00) = 10.00
    assert updated_receipt.total_amount == Decimal("10.00")
    mock_session.delete.assert_called_once_with(item)
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_delete_item_nonexistent_item(
    receipt_service: ReceiptService, mock_session: AsyncMock
) -> None:
    """Test deleting an item that doesn't exist in the receipt."""
    # Arrange
    receipt = Receipt(
        id=1,
        store_name="Test Store",
        total_amount=Decimal("10.00"),
        currency="$",
        image_path="/path/to/image.jpg",
        items=[],  # No items
    )
    mock_session.scalar.return_value = receipt
    mock_session.refresh = AsyncMock()

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await receipt_service.delete_item(
            receipt_id=1, item_id=999, user_id=TEST_USER_ID
        )
    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_item_nonexistent_receipt(
    receipt_service: ReceiptService, mock_session: AsyncMock
) -> None:
    """Test deleting an item from a receipt that doesn't exist."""
    # Arrange
    mock_session.scalar.return_value = None

    # Act & Assert
    with pytest.raises(NotFoundError) as exc_info:
        await receipt_service.delete_item(
            receipt_id=999, item_id=1, user_id=TEST_USER_ID
        )
    assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_item_currency_mismatch(
    receipt_service: ReceiptService, mock_session: AsyncMock
) -> None:
    """Test creating an item with currency that doesn't match the receipt."""
    # Arrange
    receipt = Receipt(
        id=1,
        store_name="Test Store",
        total_amount=Decimal("10.00"),
        currency="$",  # Receipt uses dollars
        image_path="/path/to/image.jpg",
        items=[],
    )
    mock_session.scalar.return_value = receipt
    mock_session.refresh = AsyncMock()

    item_data = ReceiptItemCreateRequest(
        name="New Item",
        quantity=1,
        unit_price=Decimal("5.00"),
        currency="€",  # Item uses euros - mismatch!
    )

    # Act & Assert
    with pytest.raises(BadRequestError) as exc_info:
        await receipt_service.create_item(
            receipt_id=1, item_in=item_data, user_id=TEST_USER_ID
        )
    assert "does not match" in str(exc_info.value)


# Filter Tests


@pytest.mark.asyncio
async def test_list_receipts_with_search_filter(
    receipt_service: ReceiptService, mock_session: AsyncMock
) -> None:
    """Test listing receipts with search filter."""
    # Arrange
    receipts = [
        Receipt(
            id=1,
            store_name="Grocery Store",
            total_amount=Decimal("50.00"),
            currency="$",
            image_path="/path/1.jpg",
        ),
    ]

    mock_exec_result = MagicMock()
    mock_exec_result.all.return_value = receipts
    mock_session.exec = AsyncMock(return_value=mock_exec_result)
    mock_session.refresh = AsyncMock()

    # Act
    result = await receipt_service.list(
        filters={"search": "grocery"}, user_id=TEST_USER_ID
    )

    # Assert
    assert len(result) == 1
    mock_session.exec.assert_called_once()


@pytest.mark.asyncio
async def test_list_receipts_with_amount_filters(
    receipt_service: ReceiptService, mock_session: AsyncMock
) -> None:
    """Test listing receipts with min/max amount filters."""
    # Arrange
    receipts = [
        Receipt(
            id=1,
            store_name="Store",
            total_amount=Decimal("75.00"),
            currency="$",
            image_path="/path/1.jpg",
        ),
    ]

    mock_exec_result = MagicMock()
    mock_exec_result.all.return_value = receipts
    mock_session.exec = AsyncMock(return_value=mock_exec_result)
    mock_session.refresh = AsyncMock()

    # Act
    result = await receipt_service.list(
        filters={"min_amount": Decimal("50.00"), "max_amount": Decimal("100.00")},
        user_id=TEST_USER_ID,
    )

    # Assert
    assert len(result) == 1
    mock_session.exec.assert_called_once()


@pytest.mark.asyncio
async def test_list_receipts_with_no_filters(
    receipt_service: ReceiptService, mock_session: AsyncMock
) -> None:
    """Test listing receipts without any filters returns all receipts."""
    # Arrange
    receipts = [
        Receipt(
            id=i,
            store_name=f"Store {i}",
            total_amount=Decimal(f"{10.00 * i}"),
            currency="$",
            image_path=f"/path/{i}.jpg",
        )
        for i in range(1, 4)
    ]

    mock_exec_result = MagicMock()
    mock_exec_result.all.return_value = receipts
    mock_session.exec = AsyncMock(return_value=mock_exec_result)
    mock_session.refresh = AsyncMock()

    # Act
    result = await receipt_service.list(filters=None, user_id=TEST_USER_ID)

    # Assert
    assert len(result) == 3
    mock_session.exec.assert_called_once()

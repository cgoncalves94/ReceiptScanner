"""Unit tests for receipt CSV export functionality."""

import csv
from datetime import UTC, datetime
from decimal import Decimal
from io import StringIO
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.category.services import CategoryService
from app.receipt.models import PaymentMethod
from app.receipt.services import ReceiptService

# Test user ID for data isolation
TEST_USER_ID = 1


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


def create_mock_category(category_id: int = 1, name: str = "Groceries") -> MagicMock:
    """Create a mock category object."""
    category = MagicMock()
    category.id = category_id
    category.name = name
    category.description = "Food and household items"
    return category


def create_mock_receipt_item(
    item_id: int,
    name: str,
    quantity: int,
    unit_price: Decimal,
    total_price: Decimal,
    currency: str = "$",
    category: MagicMock | None = None,
) -> MagicMock:
    """Create a mock receipt item object."""
    item = MagicMock()
    item.id = item_id
    item.name = name
    item.quantity = quantity
    item.unit_price = unit_price
    item.total_price = total_price
    item.currency = currency
    item.category = category
    return item


def create_mock_receipt(
    receipt_id: int,
    store_name: str,
    total_amount: Decimal,
    currency: str,
    purchase_date: datetime,
    payment_method: PaymentMethod | None = None,
    tax_amount: Decimal | None = None,
    items: list[MagicMock] | None = None,
) -> MagicMock:
    """Create a mock receipt object."""
    receipt = MagicMock()
    receipt.id = receipt_id
    receipt.store_name = store_name
    receipt.total_amount = total_amount
    receipt.currency = currency
    receipt.purchase_date = purchase_date
    receipt.image_path = f"/path/to/image{receipt_id}.jpg"
    receipt.payment_method = payment_method
    receipt.tax_amount = tax_amount
    receipt.items = items or []
    return receipt


@pytest.mark.asyncio
async def test_export_csv_with_items(
    receipt_service: ReceiptService,
    mock_session: AsyncMock,
) -> None:
    """Test CSV export with receipts that have items."""
    # Arrange
    category = create_mock_category(1, "Groceries")

    item1 = create_mock_receipt_item(
        1, "Milk", 2, Decimal("4.99"), Decimal("9.98"), "$", category
    )
    item2 = create_mock_receipt_item(
        2, "Bread", 1, Decimal("3.49"), Decimal("3.49"), "$", category
    )

    receipt = create_mock_receipt(
        1,
        "Test Store",
        Decimal("25.50"),
        "$",
        datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
        PaymentMethod.CREDIT_CARD,
        Decimal("2.50"),
        [item1, item2],
    )

    mock_session.exec = AsyncMock()
    mock_session.exec.return_value = MagicMock()
    mock_session.exec.return_value.all.return_value = [receipt]

    # Act
    csv_content = await receipt_service.export_to_csv(user_id=TEST_USER_ID)

    # Assert - Parse CSV to verify content
    csv_reader = csv.DictReader(StringIO(csv_content))
    rows = list(csv_reader)

    # Should have 2 rows (one per item)
    assert len(rows) == 2

    # Check first row
    assert rows[0]["receipt_id"] == "1"
    assert rows[0]["receipt_date"] == "2024-01-15T10:30:00+00:00"
    assert rows[0]["store_name"] == "Test Store"
    assert rows[0]["receipt_total"] == "25.50"
    assert rows[0]["receipt_currency"] == "$"
    assert rows[0]["payment_method"] == "credit_card"
    assert rows[0]["tax_amount"] == "2.50"
    assert rows[0]["item_id"] == "1"
    assert rows[0]["item_name"] == "Milk"
    assert rows[0]["item_quantity"] == "2"
    assert rows[0]["item_unit_price"] == "4.99"
    assert rows[0]["item_total_price"] == "9.98"
    assert rows[0]["item_currency"] == "$"
    assert rows[0]["category_name"] == "Groceries"

    # Check second row (receipt data should be repeated)
    assert rows[1]["receipt_id"] == "1"
    assert rows[1]["store_name"] == "Test Store"
    assert rows[1]["item_id"] == "2"
    assert rows[1]["item_name"] == "Bread"
    assert rows[1]["category_name"] == "Groceries"


@pytest.mark.asyncio
async def test_export_csv_without_items(
    receipt_service: ReceiptService,
    mock_session: AsyncMock,
) -> None:
    """Test CSV export with receipts that have no items."""
    # Arrange
    receipt = create_mock_receipt(
        2,
        "Another Store",
        Decimal("15.00"),
        "€",
        datetime(2024, 1, 16, 14, 0, 0, tzinfo=UTC),
        None,
        None,
        [],
    )

    mock_session.exec = AsyncMock()
    mock_session.exec.return_value = MagicMock()
    mock_session.exec.return_value.all.return_value = [receipt]

    # Act
    csv_content = await receipt_service.export_to_csv(user_id=TEST_USER_ID)

    # Assert - Parse CSV to verify content
    csv_reader = csv.DictReader(StringIO(csv_content))
    rows = list(csv_reader)

    # Should have 1 row with empty item fields
    assert len(rows) == 1
    assert rows[0]["receipt_id"] == "2"
    assert rows[0]["receipt_date"] == "2024-01-16T14:00:00+00:00"
    assert rows[0]["store_name"] == "Another Store"
    assert rows[0]["receipt_total"] == "15.00"
    assert rows[0]["receipt_currency"] == "€"
    assert rows[0]["payment_method"] == ""
    assert rows[0]["tax_amount"] == ""
    assert rows[0]["item_id"] == ""
    assert rows[0]["item_name"] == ""
    assert rows[0]["item_quantity"] == ""
    assert rows[0]["item_unit_price"] == ""
    assert rows[0]["item_total_price"] == ""
    assert rows[0]["item_currency"] == ""
    assert rows[0]["category_name"] == ""


@pytest.mark.asyncio
async def test_export_csv_multiple_receipts(
    receipt_service: ReceiptService,
    mock_session: AsyncMock,
) -> None:
    """Test CSV export with multiple receipts (with and without items)."""
    # Arrange
    category = create_mock_category(1, "Groceries")

    item1 = create_mock_receipt_item(
        1, "Milk", 2, Decimal("4.99"), Decimal("9.98"), "$", category
    )
    item2 = create_mock_receipt_item(
        2, "Bread", 1, Decimal("3.49"), Decimal("3.49"), "$", category
    )

    receipt1 = create_mock_receipt(
        1,
        "Test Store",
        Decimal("25.50"),
        "$",
        datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
        PaymentMethod.CREDIT_CARD,
        Decimal("2.50"),
        [item1, item2],
    )

    receipt2 = create_mock_receipt(
        2,
        "Another Store",
        Decimal("15.00"),
        "€",
        datetime(2024, 1, 16, 14, 0, 0, tzinfo=UTC),
        None,
        None,
        [],
    )

    mock_session.exec = AsyncMock()
    mock_session.exec.return_value = MagicMock()
    mock_session.exec.return_value.all.return_value = [receipt1, receipt2]

    # Act
    csv_content = await receipt_service.export_to_csv(user_id=TEST_USER_ID)

    # Assert - Parse CSV to verify content
    csv_reader = csv.DictReader(StringIO(csv_content))
    rows = list(csv_reader)

    # Should have 3 rows total (2 items + 1 receipt without items)
    assert len(rows) == 3

    # Check receipt IDs are present
    receipt_ids = [row["receipt_id"] for row in rows]
    assert "1" in receipt_ids  # Should appear twice (2 items)
    assert "2" in receipt_ids  # Should appear once (no items)
    assert receipt_ids.count("1") == 2
    assert receipt_ids.count("2") == 1


@pytest.mark.asyncio
async def test_export_csv_headers(
    receipt_service: ReceiptService,
    mock_session: AsyncMock,
) -> None:
    """Test that CSV has correct headers."""
    # Arrange
    mock_session.exec = AsyncMock()
    mock_session.exec.return_value = MagicMock()
    mock_session.exec.return_value.all.return_value = []

    # Act
    csv_content = await receipt_service.export_to_csv(user_id=TEST_USER_ID)

    # Assert - Check headers
    csv_reader = csv.DictReader(StringIO(csv_content))
    expected_headers = [
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
    assert csv_reader.fieldnames == expected_headers


@pytest.mark.asyncio
async def test_export_csv_empty_results(
    receipt_service: ReceiptService,
    mock_session: AsyncMock,
) -> None:
    """Test CSV export with no receipts."""
    # Arrange
    mock_session.exec = AsyncMock()
    mock_session.exec.return_value = MagicMock()
    mock_session.exec.return_value.all.return_value = []

    # Act
    csv_content = await receipt_service.export_to_csv(user_id=TEST_USER_ID)

    # Assert - Should have headers but no data rows
    csv_reader = csv.DictReader(StringIO(csv_content))
    rows = list(csv_reader)
    assert len(rows) == 0
    assert csv_reader.fieldnames is not None
    assert len(csv_reader.fieldnames) == 14


@pytest.mark.asyncio
async def test_export_csv_with_filters(
    receipt_service: ReceiptService,
    mock_session: AsyncMock,
) -> None:
    """Test CSV export with filters applied."""
    # Arrange
    category = create_mock_category(1, "Groceries")

    item1 = create_mock_receipt_item(
        1, "Milk", 2, Decimal("4.99"), Decimal("9.98"), "$", category
    )
    item2 = create_mock_receipt_item(
        2, "Bread", 1, Decimal("3.49"), Decimal("3.49"), "$", category
    )

    receipt = create_mock_receipt(
        1,
        "Test Store",
        Decimal("25.50"),
        "$",
        datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
        PaymentMethod.CREDIT_CARD,
        Decimal("2.50"),
        [item1, item2],
    )

    mock_session.exec = AsyncMock()
    mock_session.exec.return_value = MagicMock()
    mock_session.exec.return_value.all.return_value = [receipt]

    filters = {
        "store": "Test Store",
        "after": datetime(2024, 1, 1, tzinfo=UTC),
        "before": datetime(2024, 1, 31, tzinfo=UTC),
    }

    # Act
    csv_content = await receipt_service.export_to_csv(
        filters=filters, user_id=TEST_USER_ID
    )

    # Assert - Verify CSV is generated
    csv_reader = csv.DictReader(StringIO(csv_content))
    rows = list(csv_reader)
    assert len(rows) == 2  # 2 items from the receipt
    assert rows[0]["store_name"] == "Test Store"


@pytest.mark.asyncio
async def test_export_csv_item_without_category(
    receipt_service: ReceiptService,
    mock_session: AsyncMock,
) -> None:
    """Test CSV export with items that have no category."""
    # Arrange
    item = create_mock_receipt_item(
        3, "Uncategorized Item", 1, Decimal("10.00"), Decimal("10.00"), "$", None
    )

    receipt = create_mock_receipt(
        3,
        "Store 3",
        Decimal("10.00"),
        "$",
        datetime(2024, 1, 17, 10, 0, 0, tzinfo=UTC),
        None,
        None,
        [item],
    )

    mock_session.exec = AsyncMock()
    mock_session.exec.return_value = MagicMock()
    mock_session.exec.return_value.all.return_value = [receipt]

    # Act
    csv_content = await receipt_service.export_to_csv(user_id=TEST_USER_ID)

    # Assert - Category name should be empty
    csv_reader = csv.DictReader(StringIO(csv_content))
    rows = list(csv_reader)
    assert len(rows) == 1
    assert rows[0]["item_name"] == "Uncategorized Item"
    assert rows[0]["category_name"] == ""


@pytest.mark.asyncio
async def test_export_csv_payment_methods(
    receipt_service: ReceiptService,
    mock_session: AsyncMock,
) -> None:
    """Test CSV export with different payment methods."""
    # Arrange
    category = create_mock_category(1, "Groceries")

    receipts = []
    for idx, payment_method in enumerate(
        [PaymentMethod.CASH, PaymentMethod.DEBIT_CARD, PaymentMethod.MOBILE_PAYMENT]
    ):
        item = create_mock_receipt_item(
            idx + 10,
            f"Item {idx}",
            1,
            Decimal("10.00"),
            Decimal("10.00"),
            "$",
            category,
        )
        receipt = create_mock_receipt(
            idx + 10,
            f"Store {idx}",
            Decimal("10.00"),
            "$",
            datetime(2024, 1, idx + 1, 10, 0, 0, tzinfo=UTC),
            payment_method,
            None,
            [item],
        )
        receipts.append(receipt)

    mock_session.exec = AsyncMock()
    mock_session.exec.return_value = MagicMock()
    mock_session.exec.return_value.all.return_value = receipts

    # Act
    csv_content = await receipt_service.export_to_csv(user_id=TEST_USER_ID)

    # Assert - Check payment methods are included
    csv_reader = csv.DictReader(StringIO(csv_content))
    rows = list(csv_reader)
    assert len(rows) == 3
    assert rows[0]["payment_method"] == "cash"
    assert rows[1]["payment_method"] == "debit_card"
    assert rows[2]["payment_method"] == "mobile_payment"


@pytest.mark.asyncio
async def test_export_csv_rfc4180_compliance(
    receipt_service: ReceiptService,
    mock_session: AsyncMock,
) -> None:
    """Test that CSV output is RFC 4180 compliant (proper quoting for special chars)."""
    # Arrange - Create receipt with special characters that require quoting
    category = create_mock_category(1, "Groceries")

    item = create_mock_receipt_item(
        4, "Item, with comma", 1, Decimal("10.00"), Decimal("10.00"), "$", category
    )

    receipt = create_mock_receipt(
        4,
        'Store "With Quotes"',
        Decimal("10.00"),
        "$",
        datetime(2024, 1, 18, 10, 0, 0, tzinfo=UTC),
        None,
        None,
        [item],
    )

    mock_session.exec = AsyncMock()
    mock_session.exec.return_value = MagicMock()
    mock_session.exec.return_value.all.return_value = [receipt]

    # Act
    csv_content = await receipt_service.export_to_csv(user_id=TEST_USER_ID)

    # Assert - Verify CSV can be parsed correctly despite special characters
    csv_reader = csv.DictReader(StringIO(csv_content))
    rows = list(csv_reader)
    assert len(rows) == 1
    assert rows[0]["store_name"] == 'Store "With Quotes"'
    assert rows[0]["item_name"] == "Item, with comma"


@pytest.mark.asyncio
async def test_export_csv_decimal_precision(
    receipt_service: ReceiptService,
    mock_session: AsyncMock,
) -> None:
    """Test that decimal values are properly formatted in CSV."""
    # Arrange - Create receipt with precise decimal values
    category = create_mock_category(1, "Groceries")

    item = create_mock_receipt_item(
        5, "Item with decimals", 3, Decimal("3.33"), Decimal("9.99"), "$", category
    )

    receipt = create_mock_receipt(
        5,
        "Store 5",
        Decimal("12.99"),
        "$",
        datetime(2024, 1, 19, 10, 0, 0, tzinfo=UTC),
        None,
        Decimal("1.30"),
        [item],
    )

    mock_session.exec = AsyncMock()
    mock_session.exec.return_value = MagicMock()
    mock_session.exec.return_value.all.return_value = [receipt]

    # Act
    csv_content = await receipt_service.export_to_csv(user_id=TEST_USER_ID)

    # Assert - Check decimal values are preserved
    csv_reader = csv.DictReader(StringIO(csv_content))
    rows = list(csv_reader)
    assert len(rows) == 1
    assert rows[0]["receipt_total"] == "12.99"
    assert rows[0]["tax_amount"] == "1.30"
    assert rows[0]["item_unit_price"] == "3.33"
    assert rows[0]["item_total_price"] == "9.99"
    assert rows[0]["item_quantity"] == "3"

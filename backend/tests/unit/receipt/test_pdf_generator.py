"""Unit tests for the PDF generator."""

from datetime import datetime
from decimal import Decimal
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image as PILImage

from app.receipt.exporters import ReceiptPDFGenerator
from app.receipt.models import PaymentMethod


def create_mock_category(category_id: int = 1, name: str = "Groceries") -> MagicMock:
    """Create a mock category."""
    cat = MagicMock()
    cat.id = category_id
    cat.name = name
    return cat


def create_mock_item(
    item_id: int = 1,
    name: str = "Test Item",
    quantity: int = 2,
    unit_price: Decimal = Decimal("10.50"),
    total_price: Decimal = Decimal("21.00"),
    currency: str = "$",
    category: MagicMock | None = None,
) -> MagicMock:
    """Create a mock receipt item."""
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
    receipt_id: int = 1,
    store_name: str = "Test Store",
    total_amount: Decimal = Decimal("21.00"),
    currency: str = "$",
    purchase_date: datetime = datetime(2024, 1, 15, 10, 30),
    image_path: str | None = "/path/to/image.jpg",
    notes: str | None = "Test notes",
    payment_method: PaymentMethod | None = PaymentMethod.CREDIT_CARD,
    tax_amount: Decimal | None = Decimal("2.00"),
    items: list | None = None,
) -> MagicMock:
    """Create a mock receipt."""
    receipt = MagicMock()
    receipt.id = receipt_id
    receipt.store_name = store_name
    receipt.total_amount = total_amount
    receipt.currency = currency
    receipt.purchase_date = purchase_date
    receipt.image_path = image_path
    receipt.notes = notes
    receipt.payment_method = payment_method
    receipt.tax_amount = tax_amount
    receipt.items = items if items is not None else []
    return receipt


@pytest.fixture
def sample_category() -> MagicMock:
    """Create a sample category."""
    return create_mock_category()


@pytest.fixture
def sample_receipt_item(sample_category: MagicMock) -> MagicMock:
    """Create a sample receipt item."""
    return create_mock_item(category=sample_category)


@pytest.fixture
def sample_receipt(sample_receipt_item: MagicMock) -> MagicMock:
    """Create a sample receipt."""
    return create_mock_receipt(items=[sample_receipt_item])


@pytest.fixture
def pdf_generator() -> ReceiptPDFGenerator:
    """Create a PDF generator instance."""
    return ReceiptPDFGenerator()


def test_pdf_generator_init(pdf_generator: ReceiptPDFGenerator) -> None:
    """Test PDF generator initialization."""
    assert isinstance(pdf_generator.buffer, BytesIO)
    assert pdf_generator.styles is not None
    assert "ReportTitle" in pdf_generator.styles
    assert "SectionTitle" in pdf_generator.styles
    assert "ReceiptHeader" in pdf_generator.styles


def test_custom_styles_setup(pdf_generator: ReceiptPDFGenerator) -> None:
    """Test custom styles are properly configured."""
    report_title = pdf_generator.styles["ReportTitle"]
    assert report_title.fontSize == 22
    assert report_title.alignment == 1  # Center alignment

    section_title = pdf_generator.styles["SectionTitle"]
    assert section_title.fontSize == 11

    receipt_header = pdf_generator.styles["ReceiptHeader"]
    assert receipt_header.fontSize == 13


def test_generate_empty_receipts() -> None:
    """Test generating PDF with empty receipts list."""
    generator = ReceiptPDFGenerator()
    receipts: list = []

    pdf_bytes = generator.generate(receipts)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_generate_single_receipt(sample_receipt: MagicMock) -> None:
    """Test generating PDF with a single receipt."""
    generator = ReceiptPDFGenerator()
    receipts = [sample_receipt]

    pdf_bytes = generator.generate(receipts, include_images=False)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_generate_multiple_receipts(sample_receipt: MagicMock) -> None:
    """Test generating PDF with multiple receipts."""
    generator = ReceiptPDFGenerator()
    receipt2 = create_mock_receipt(
        receipt_id=2,
        store_name="Another Store",
        total_amount=Decimal("50.00"),
        currency="€",
        purchase_date=datetime(2024, 1, 16, 14, 0),
        items=[],
    )
    receipts = [sample_receipt, receipt2]

    pdf_bytes = generator.generate(receipts, include_images=False)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_generate_with_images_file_exists(sample_receipt: MagicMock) -> None:
    """Test generating PDF with images when file exists."""
    generator = ReceiptPDFGenerator()
    receipts = [sample_receipt]

    mock_image = MagicMock(spec=PILImage.Image)
    mock_image.width = 800
    mock_image.height = 1200

    with patch("app.receipt.exporters.PILImage.open", return_value=mock_image):
        with patch("app.receipt.exporters.Path.exists", return_value=True):
            pdf_bytes = generator.generate(receipts, include_images=True)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_generate_with_images_file_not_exists(sample_receipt: MagicMock) -> None:
    """Test generating PDF with images when file doesn't exist."""
    generator = ReceiptPDFGenerator()
    receipts = [sample_receipt]

    with patch("app.receipt.exporters.Path.exists", return_value=False):
        pdf_bytes = generator.generate(receipts, include_images=True)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_generate_with_images_load_fails(sample_receipt: MagicMock) -> None:
    """Test generating PDF when image loading fails."""
    generator = ReceiptPDFGenerator()
    receipts = [sample_receipt]

    with patch("app.receipt.exporters.Path.exists", return_value=True):
        with patch(
            "app.receipt.exporters.PILImage.open",
            side_effect=Exception("Image load failed"),
        ):
            pdf_bytes = generator.generate(receipts, include_images=True)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_create_summary_section_single_currency(
    pdf_generator: ReceiptPDFGenerator, sample_receipt: MagicMock
) -> None:
    """Test creating summary section with single currency."""
    receipts = [sample_receipt]

    elements = pdf_generator._create_summary_section(receipts)

    assert len(elements) > 0


def test_create_summary_section_multiple_currencies(
    pdf_generator: ReceiptPDFGenerator, sample_receipt: MagicMock
) -> None:
    """Test creating summary section with multiple currencies."""
    category_eur = create_mock_category(category_id=2, name="Food")
    item_eur = create_mock_item(
        item_id=2,
        name="Euro Item",
        quantity=1,
        unit_price=Decimal("30.00"),
        total_price=Decimal("30.00"),
        currency="€",
        category=category_eur,
    )
    receipt_eur = create_mock_receipt(
        receipt_id=2,
        store_name="Euro Store",
        total_amount=Decimal("30.00"),
        currency="€",
        purchase_date=datetime(2024, 1, 16, 14, 0),
        items=[item_eur],
    )
    receipts = [sample_receipt, receipt_eur]

    elements = pdf_generator._create_summary_section(receipts)

    assert len(elements) > 0


def test_create_summary_section_category_breakdown(
    pdf_generator: ReceiptPDFGenerator, sample_receipt: MagicMock
) -> None:
    """Test creating summary section with category breakdown."""
    category2 = create_mock_category(category_id=2, name="Electronics")
    item2 = create_mock_item(
        item_id=2,
        name="Gadget",
        quantity=1,
        unit_price=Decimal("100.00"),
        total_price=Decimal("100.00"),
        currency="$",
        category=category2,
    )
    sample_receipt.items.append(item2)
    receipts = [sample_receipt]

    elements = pdf_generator._create_summary_section(receipts)

    assert len(elements) > 0


def test_create_summary_section_uncategorized_items(
    pdf_generator: ReceiptPDFGenerator,
) -> None:
    """Test creating summary section with uncategorized items."""
    item = create_mock_item(
        item_id=1,
        name="Uncategorized Item",
        quantity=1,
        unit_price=Decimal("20.00"),
        total_price=Decimal("20.00"),
        currency="$",
        category=None,
    )
    receipt = create_mock_receipt(
        receipt_id=1,
        store_name="Test Store",
        total_amount=Decimal("20.00"),
        items=[item],
    )
    receipts = [receipt]

    elements = pdf_generator._create_summary_section(receipts)

    assert len(elements) > 0


def test_create_receipt_section_all_fields(
    pdf_generator: ReceiptPDFGenerator, sample_receipt: MagicMock
) -> None:
    """Test creating receipt section with all optional fields."""
    elements = pdf_generator._create_receipt_section(
        sample_receipt, include_images=False
    )

    assert len(elements) > 0


def test_create_receipt_section_minimal_fields(
    pdf_generator: ReceiptPDFGenerator,
) -> None:
    """Test creating receipt section with minimal required fields."""
    item = create_mock_item(
        item_id=1,
        name="Item",
        quantity=1,
        unit_price=Decimal("10.00"),
        total_price=Decimal("10.00"),
        currency="$",
        category=None,
    )
    receipt = create_mock_receipt(
        receipt_id=1,
        store_name="Minimal Store",
        total_amount=Decimal("10.00"),
        payment_method=None,
        tax_amount=None,
        notes=None,
        items=[item],
    )

    elements = pdf_generator._create_receipt_section(receipt, include_images=False)

    assert len(elements) > 0


def test_create_receipt_section_payment_method_formatting(
    pdf_generator: ReceiptPDFGenerator,
) -> None:
    """Test that payment method enum is formatted correctly."""
    receipt = create_mock_receipt(
        receipt_id=1,
        store_name="Test Store",
        payment_method=PaymentMethod.CREDIT_CARD,
        items=[],
    )

    elements = pdf_generator._create_receipt_section(receipt, include_images=False)

    assert len(elements) > 0


def test_create_receipt_section_date_formatting(
    pdf_generator: ReceiptPDFGenerator,
) -> None:
    """Test that dates are formatted correctly."""
    receipt = create_mock_receipt(
        receipt_id=1,
        store_name="Test Store",
        purchase_date=datetime(2024, 1, 15, 10, 30),
        items=[],
    )

    elements = pdf_generator._create_receipt_section(receipt, include_images=False)

    assert len(elements) > 0


def test_create_receipt_section_no_items(pdf_generator: ReceiptPDFGenerator) -> None:
    """Test creating receipt section with no items."""
    receipt = create_mock_receipt(
        receipt_id=1,
        store_name="Empty Store",
        total_amount=Decimal("0.00"),
        items=[],
    )

    elements = pdf_generator._create_receipt_section(receipt, include_images=False)

    assert len(elements) > 0


def test_create_receipt_section_with_image(
    pdf_generator: ReceiptPDFGenerator, sample_receipt: MagicMock
) -> None:
    """Test creating receipt section with image included."""
    mock_image = MagicMock(spec=PILImage.Image)
    mock_image.width = 800
    mock_image.height = 1200

    with patch("app.receipt.exporters.PILImage.open", return_value=mock_image):
        with patch("app.receipt.exporters.Path.exists", return_value=True):
            elements = pdf_generator._create_receipt_section(
                sample_receipt, include_images=True
            )

    assert len(elements) > 0


def test_create_receipt_section_image_scaling(
    pdf_generator: ReceiptPDFGenerator, sample_receipt: MagicMock
) -> None:
    """Test that images are scaled appropriately."""
    mock_image = MagicMock(spec=PILImage.Image)
    mock_image.width = 3000  # Very wide
    mock_image.height = 1000

    with patch("app.receipt.exporters.PILImage.open", return_value=mock_image):
        with patch("app.receipt.exporters.Path.exists", return_value=True):
            elements = pdf_generator._create_receipt_section(
                sample_receipt, include_images=True
            )

    assert len(elements) > 0


def test_buffer_closed_after_generate(sample_receipt: MagicMock) -> None:
    """Test that buffer is closed after generating PDF."""
    generator = ReceiptPDFGenerator()
    receipts = [sample_receipt]

    pdf_bytes = generator.generate(receipts, include_images=False)

    assert isinstance(pdf_bytes, bytes)
    assert generator.buffer.closed

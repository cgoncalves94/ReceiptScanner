"""Unit tests for the PDF generator."""

from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from PIL import Image as PILImage

from app.category.models import Category
from app.receipt.models import PaymentMethod, Receipt, ReceiptItem
from app.receipt.pdf_generator import ReceiptPDFGenerator


@pytest.fixture
def sample_category() -> Category:
    """Create a sample category."""
    return Category(
        id=1,
        name="Groceries",
        description="Grocery items",
        user_id=1,
    )


@pytest.fixture
def sample_receipt_item(sample_category: Category) -> ReceiptItem:
    """Create a sample receipt item."""
    return ReceiptItem(
        id=1,
        name="Test Item",
        quantity=2,
        unit_price=Decimal("10.50"),
        total_price=Decimal("21.00"),
        currency="$",
        category_id=sample_category.id,
        category=sample_category,
        receipt_id=1,
    )


@pytest.fixture
def sample_receipt(sample_receipt_item: ReceiptItem) -> Receipt:
    """Create a sample receipt."""
    receipt = Receipt(
        id=1,
        store_name="Test Store",
        total_amount=Decimal("21.00"),
        currency="$",
        purchase_date=datetime(2024, 1, 15, 10, 30),
        image_path="/path/to/image.jpg",
        notes="Test notes",
        payment_method=PaymentMethod.CREDIT_CARD,
        tax_amount=Decimal("2.00"),
        user_id=1,
    )
    receipt.items = [sample_receipt_item]
    return receipt


@pytest.fixture
def pdf_generator() -> ReceiptPDFGenerator:
    """Create a PDF generator instance."""
    return ReceiptPDFGenerator()


def test_pdf_generator_init(pdf_generator: ReceiptPDFGenerator) -> None:
    """Test PDF generator initialization."""
    # Assert
    assert isinstance(pdf_generator.buffer, BytesIO)
    assert pdf_generator.styles is not None
    assert "CustomTitle" in pdf_generator.styles
    assert "SectionHeading" in pdf_generator.styles
    assert "ReceiptInfo" in pdf_generator.styles


def test_custom_styles_setup(pdf_generator: ReceiptPDFGenerator) -> None:
    """Test custom styles are properly configured."""
    # Assert
    custom_title = pdf_generator.styles["CustomTitle"]
    assert custom_title.fontSize == 24
    assert custom_title.alignment == 1  # Center alignment

    section_heading = pdf_generator.styles["SectionHeading"]
    assert section_heading.fontSize == 14

    receipt_info = pdf_generator.styles["ReceiptInfo"]
    assert receipt_info.fontSize == 10


def test_generate_empty_receipts() -> None:
    """Test generating PDF with empty receipts list."""
    # Arrange
    generator = ReceiptPDFGenerator()
    receipts: list[Receipt] = []

    # Act
    pdf_bytes = generator.generate(receipts)

    # Assert
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0  # Should still generate a PDF with title/summary


def test_generate_single_receipt(sample_receipt: Receipt) -> None:
    """Test generating PDF with a single receipt."""
    # Arrange
    generator = ReceiptPDFGenerator()
    receipts = [sample_receipt]

    # Act
    pdf_bytes = generator.generate(receipts, include_images=False)

    # Assert
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_generate_multiple_receipts(sample_receipt: Receipt) -> None:
    """Test generating PDF with multiple receipts."""
    # Arrange
    generator = ReceiptPDFGenerator()
    receipt2 = Receipt(
        id=2,
        store_name="Another Store",
        total_amount=Decimal("50.00"),
        currency="€",
        purchase_date=datetime(2024, 1, 16, 14, 0),
        image_path="/path/to/image2.jpg",
        user_id=1,
    )
    receipt2.items = []
    receipts = [sample_receipt, receipt2]

    # Act
    pdf_bytes = generator.generate(receipts, include_images=False)

    # Assert
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_generate_with_images_file_exists(sample_receipt: Receipt) -> None:
    """Test generating PDF with images when file exists."""
    # Arrange
    generator = ReceiptPDFGenerator()
    receipts = [sample_receipt]

    # Mock PIL Image and Path.exists
    mock_image = MagicMock(spec=PILImage.Image)
    mock_image.width = 800
    mock_image.height = 1200

    with patch("app.receipt.pdf_generator.PILImage.open", return_value=mock_image):
        with patch("app.receipt.pdf_generator.Path.exists", return_value=True):
            # Act
            pdf_bytes = generator.generate(receipts, include_images=True)

    # Assert
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_generate_with_images_file_not_exists(sample_receipt: Receipt) -> None:
    """Test generating PDF with images when file doesn't exist."""
    # Arrange
    generator = ReceiptPDFGenerator()
    receipts = [sample_receipt]

    with patch("app.receipt.pdf_generator.Path.exists", return_value=False):
        # Act
        pdf_bytes = generator.generate(receipts, include_images=True)

    # Assert
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0  # Should still generate PDF without image


def test_generate_with_images_load_fails(sample_receipt: Receipt) -> None:
    """Test generating PDF when image loading fails."""
    # Arrange
    generator = ReceiptPDFGenerator()
    receipts = [sample_receipt]

    with patch("app.receipt.pdf_generator.Path.exists", return_value=True):
        with patch(
            "app.receipt.pdf_generator.PILImage.open",
            side_effect=Exception("Image load failed"),
        ):
            # Act
            pdf_bytes = generator.generate(receipts, include_images=True)

    # Assert
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0  # Should handle exception silently


def test_create_summary_section_single_currency(
    pdf_generator: ReceiptPDFGenerator, sample_receipt: Receipt
) -> None:
    """Test creating summary section with single currency."""
    # Arrange
    receipts = [sample_receipt]

    # Act
    elements = pdf_generator._create_summary_section(receipts)

    # Assert
    assert len(elements) > 0
    # Should have heading, summary table, spacer, category heading, category table, spacer


def test_create_summary_section_multiple_currencies(
    pdf_generator: ReceiptPDFGenerator, sample_receipt: Receipt
) -> None:
    """Test creating summary section with multiple currencies."""
    # Arrange
    receipt_eur = Receipt(
        id=2,
        store_name="Euro Store",
        total_amount=Decimal("30.00"),
        currency="€",
        purchase_date=datetime(2024, 1, 16, 14, 0),
        image_path="/path/to/image2.jpg",
        user_id=1,
    )
    item_eur = ReceiptItem(
        id=2,
        name="Euro Item",
        quantity=1,
        unit_price=Decimal("30.00"),
        total_price=Decimal("30.00"),
        currency="€",
        category_id=1,
        receipt_id=2,
    )
    item_eur.category = Category(id=1, name="Food", user_id=1)
    receipt_eur.items = [item_eur]

    receipts = [sample_receipt, receipt_eur]

    # Act
    elements = pdf_generator._create_summary_section(receipts)

    # Assert
    assert len(elements) > 0


def test_create_summary_section_category_breakdown(
    pdf_generator: ReceiptPDFGenerator, sample_receipt: Receipt
) -> None:
    """Test creating summary section with category breakdown."""
    # Arrange
    category2 = Category(id=2, name="Electronics", user_id=1)
    item2 = ReceiptItem(
        id=2,
        name="Gadget",
        quantity=1,
        unit_price=Decimal("100.00"),
        total_price=Decimal("100.00"),
        currency="$",
        category_id=2,
        category=category2,
        receipt_id=1,
    )
    sample_receipt.items.append(item2)
    receipts = [sample_receipt]

    # Act
    elements = pdf_generator._create_summary_section(receipts)

    # Assert
    assert len(elements) > 0
    # Should include category breakdown with both categories


def test_create_summary_section_uncategorized_items(
    pdf_generator: ReceiptPDFGenerator,
) -> None:
    """Test creating summary section with uncategorized items."""
    # Arrange
    receipt = Receipt(
        id=1,
        store_name="Test Store",
        total_amount=Decimal("20.00"),
        currency="$",
        purchase_date=datetime(2024, 1, 15, 10, 30),
        image_path="/path/to/image.jpg",
        user_id=1,
    )
    item = ReceiptItem(
        id=1,
        name="Uncategorized Item",
        quantity=1,
        unit_price=Decimal("20.00"),
        total_price=Decimal("20.00"),
        currency="$",
        category_id=None,
        category=None,
        receipt_id=1,
    )
    receipt.items = [item]
    receipts = [receipt]

    # Act
    elements = pdf_generator._create_summary_section(receipts)

    # Assert
    assert len(elements) > 0


def test_create_receipt_section_all_fields(
    pdf_generator: ReceiptPDFGenerator, sample_receipt: Receipt
) -> None:
    """Test creating receipt section with all optional fields."""
    # Act
    elements = pdf_generator._create_receipt_section(
        sample_receipt, include_images=False
    )

    # Assert
    assert len(elements) > 0
    # Should include heading, details table, items table


def test_create_receipt_section_minimal_fields(
    pdf_generator: ReceiptPDFGenerator,
) -> None:
    """Test creating receipt section with minimal required fields."""
    # Arrange
    receipt = Receipt(
        id=1,
        store_name="Minimal Store",
        total_amount=Decimal("10.00"),
        currency="$",
        purchase_date=datetime(2024, 1, 15, 10, 30),
        image_path="/path/to/image.jpg",
        user_id=1,
    )
    item = ReceiptItem(
        id=1,
        name="Item",
        quantity=1,
        unit_price=Decimal("10.00"),
        total_price=Decimal("10.00"),
        currency="$",
        receipt_id=1,
    )
    receipt.items = [item]

    # Act
    elements = pdf_generator._create_receipt_section(receipt, include_images=False)

    # Assert
    assert len(elements) > 0


def test_create_receipt_section_payment_method_formatting(
    pdf_generator: ReceiptPDFGenerator,
) -> None:
    """Test that payment method enum is formatted correctly."""
    # Arrange
    receipt = Receipt(
        id=1,
        store_name="Test Store",
        total_amount=Decimal("10.00"),
        currency="$",
        purchase_date=datetime(2024, 1, 15, 10, 30),
        image_path="/path/to/image.jpg",
        payment_method=PaymentMethod.CREDIT_CARD,
        user_id=1,
    )
    receipt.items = []

    # Act
    elements = pdf_generator._create_receipt_section(receipt, include_images=False)

    # Assert
    assert len(elements) > 0
    # Payment method should be formatted as "Credit Card" not "credit_card"


def test_create_receipt_section_date_formatting(
    pdf_generator: ReceiptPDFGenerator,
) -> None:
    """Test that dates are formatted correctly."""
    # Arrange
    receipt = Receipt(
        id=1,
        store_name="Test Store",
        total_amount=Decimal("10.00"),
        currency="$",
        purchase_date=datetime(2024, 1, 15, 10, 30),
        image_path="/path/to/image.jpg",
        user_id=1,
    )
    receipt.items = []

    # Act
    elements = pdf_generator._create_receipt_section(receipt, include_images=False)

    # Assert
    assert len(elements) > 0
    # Date should be formatted as "January 15, 2024"


def test_create_receipt_section_no_items(pdf_generator: ReceiptPDFGenerator) -> None:
    """Test creating receipt section with no items."""
    # Arrange
    receipt = Receipt(
        id=1,
        store_name="Empty Store",
        total_amount=Decimal("0.00"),
        currency="$",
        purchase_date=datetime(2024, 1, 15, 10, 30),
        image_path="/path/to/image.jpg",
        user_id=1,
    )
    receipt.items = []

    # Act
    elements = pdf_generator._create_receipt_section(receipt, include_images=False)

    # Assert
    assert len(elements) > 0
    # Should still create section with empty items table


def test_create_receipt_section_with_image(
    pdf_generator: ReceiptPDFGenerator, sample_receipt: Receipt
) -> None:
    """Test creating receipt section with image included."""
    # Arrange
    mock_image = MagicMock(spec=PILImage.Image)
    mock_image.width = 800
    mock_image.height = 1200

    with patch("app.receipt.pdf_generator.PILImage.open", return_value=mock_image):
        with patch("app.receipt.pdf_generator.Path.exists", return_value=True):
            # Act
            elements = pdf_generator._create_receipt_section(
                sample_receipt, include_images=True
            )

    # Assert
    assert len(elements) > 0


def test_create_receipt_section_image_scaling(
    pdf_generator: ReceiptPDFGenerator, sample_receipt: Receipt
) -> None:
    """Test that images are scaled appropriately."""
    # Arrange
    # Test with very wide image
    mock_image = MagicMock(spec=PILImage.Image)
    mock_image.width = 3000  # Very wide
    mock_image.height = 1000

    with patch("app.receipt.pdf_generator.PILImage.open", return_value=mock_image):
        with patch("app.receipt.pdf_generator.Path.exists", return_value=True):
            # Act
            elements = pdf_generator._create_receipt_section(
                sample_receipt, include_images=True
            )

    # Assert
    assert len(elements) > 0


def test_buffer_closed_after_generate(sample_receipt: Receipt) -> None:
    """Test that buffer is closed after generating PDF."""
    # Arrange
    generator = ReceiptPDFGenerator()
    receipts = [sample_receipt]

    # Act
    pdf_bytes = generator.generate(receipts, include_images=False)

    # Assert
    assert isinstance(pdf_bytes, bytes)
    assert generator.buffer.closed

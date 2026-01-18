"""PDF generator utility for receipt reports."""

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.receipt.models import Receipt


class ReceiptPDFGenerator:
    """Generator for creating professional PDF reports from receipt data."""

    def __init__(self) -> None:
        """Initialize the PDF generator."""
        self.buffer = BytesIO()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self) -> None:
        """Set up custom paragraph styles for the PDF."""
        # Title style
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#1a1a1a"),
                spaceAfter=30,
                alignment=1,  # Center alignment
            )
        )

        # Section heading style
        self.styles.add(
            ParagraphStyle(
                name="SectionHeading",
                parent=self.styles["Heading2"],
                fontSize=14,
                textColor=colors.HexColor("#2c3e50"),
                spaceAfter=12,
                spaceBefore=20,
            )
        )

        # Receipt info style
        self.styles.add(
            ParagraphStyle(
                name="ReceiptInfo",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#34495e"),
            )
        )

    def generate(
        self, receipts: list[Receipt], include_images: bool = False
    ) -> bytes:
        """Generate a PDF report from a list of receipts.

        Args:
            receipts: List of Receipt objects to include in the report
            include_images: Whether to embed receipt images in the PDF

        Returns:
            PDF file as bytes
        """
        # Create the PDF document
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        # Build the document content
        story = []

        # Add title
        title = Paragraph("Receipt Report", self.styles["CustomTitle"])
        story.append(title)

        # Add generation timestamp
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        timestamp_para = Paragraph(
            f"<i>Generated on {timestamp}</i>", self.styles["Normal"]
        )
        story.append(timestamp_para)
        story.append(Spacer(1, 0.3 * inch))

        # Add summary section
        story.extend(self._create_summary_section(receipts))

        # Add each receipt
        for i, receipt in enumerate(receipts):
            if i > 0:
                story.append(PageBreak())

            story.extend(
                self._create_receipt_section(receipt, include_images=include_images)
            )

        # Build the PDF
        doc.build(story)

        # Get the PDF bytes
        pdf_bytes = self.buffer.getvalue()
        self.buffer.close()

        return pdf_bytes

    def _create_summary_section(self, receipts: list[Receipt]) -> list:
        """Create the summary section with overall statistics.

        Args:
            receipts: List of receipts to summarize

        Returns:
            List of reportlab flowables for the summary section
        """
        elements = []

        # Summary heading
        heading = Paragraph("Summary", self.styles["SectionHeading"])
        elements.append(heading)

        # Calculate overall statistics
        total_receipts = len(receipts)
        total_amount_by_currency: dict[str, Decimal] = defaultdict(Decimal)
        category_totals: dict[str, Decimal] = defaultdict(Decimal)

        for receipt in receipts:
            total_amount_by_currency[receipt.currency] += receipt.total_amount

            for item in receipt.items:
                category_name = item.category.name if item.category else "Uncategorized"
                category_totals[category_name] += item.total_price

        # Create summary table
        summary_data = [
            ["Total Receipts:", str(total_receipts)],
        ]

        # Add total amounts by currency
        for currency, amount in sorted(total_amount_by_currency.items()):
            summary_data.append([f"Total Amount ({currency}):", f"{amount:.2f}"])

        summary_table = Table(summary_data, colWidths=[2.5 * inch, 2 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
                    ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 10),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2c3e50")),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(summary_table)
        elements.append(Spacer(1, 0.2 * inch))

        # Category breakdown
        if category_totals:
            category_heading = Paragraph(
                "Category Breakdown", self.styles["SectionHeading"]
            )
            elements.append(category_heading)

            category_data = [["Category", "Total Amount"]]
            for category, amount in sorted(
                category_totals.items(), key=lambda x: x[1], reverse=True
            ):
                category_data.append([category, f"{amount:.2f}"])

            category_table = Table(category_data, colWidths=[3 * inch, 2 * inch])
            category_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 11),
                        ("FONT", (0, 1), (-1, -1), "Helvetica", 10),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
                    ]
                )
            )
            elements.append(category_table)

        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _create_receipt_section(
        self, receipt: Receipt, include_images: bool = False
    ) -> list:
        """Create a section for a single receipt.

        Args:
            receipt: The receipt to render
            include_images: Whether to include the receipt image

        Returns:
            List of reportlab flowables for the receipt section
        """
        elements = []

        # Receipt heading
        heading = Paragraph(
            f"Receipt - {receipt.store_name}", self.styles["SectionHeading"]
        )
        elements.append(heading)

        # Receipt details table
        purchase_date_str = receipt.purchase_date.strftime("%B %d, %Y")
        details_data = [
            ["Store:", receipt.store_name],
            ["Date:", purchase_date_str],
            ["Total Amount:", f"{receipt.currency} {receipt.total_amount:.2f}"],
        ]

        if receipt.payment_method:
            payment_method = receipt.payment_method.value.replace("_", " ").title()
            details_data.append(["Payment Method:", payment_method])

        if receipt.tax_amount:
            details_data.append(["Tax Amount:", f"{receipt.currency} {receipt.tax_amount:.2f}"])

        if receipt.notes:
            details_data.append(["Notes:", receipt.notes])

        details_table = Table(details_data, colWidths=[2 * inch, 4.5 * inch])
        details_table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 10),
                    ("FONT", (1, 0), (1, -1), "Helvetica", 10),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#2c3e50")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(details_table)
        elements.append(Spacer(1, 0.2 * inch))

        # Items table
        items_heading = Paragraph("Items", self.styles["SectionHeading"])
        elements.append(items_heading)

        items_data = [["Item", "Category", "Qty", "Unit Price", "Total"]]

        for item in receipt.items:
            category_name = item.category.name if item.category else "Uncategorized"
            items_data.append(
                [
                    item.name,
                    category_name,
                    str(item.quantity),
                    f"{item.currency} {item.unit_price:.2f}",
                    f"{item.currency} {item.total_price:.2f}",
                ]
            )

        items_table = Table(
            items_data,
            colWidths=[2.2 * inch, 1.8 * inch, 0.6 * inch, 1 * inch, 1 * inch],
        )
        items_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
                    ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
                    ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                    ("ALIGN", (0, 0), (1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
                ]
            )
        )
        elements.append(items_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Include receipt image if requested
        if include_images and receipt.image_path:
            image_path = Path(receipt.image_path)
            if image_path.exists():
                try:
                    # Load and resize image to fit on page
                    pil_image = PILImage.open(image_path)

                    # Calculate dimensions to fit within page width
                    max_width = 6 * inch
                    max_height = 4 * inch

                    # Calculate scaling factor
                    width_ratio = max_width / pil_image.width
                    height_ratio = max_height / pil_image.height
                    scale_factor = min(width_ratio, height_ratio)

                    new_width = pil_image.width * scale_factor
                    new_height = pil_image.height * scale_factor

                    # Add image heading
                    image_heading = Paragraph("Receipt Image", self.styles["SectionHeading"])
                    elements.append(image_heading)

                    # Add the image
                    img = Image(str(image_path), width=new_width, height=new_height)
                    elements.append(img)
                    elements.append(Spacer(1, 0.2 * inch))

                except Exception:
                    # If image fails to load, skip it silently
                    pass

        return elements

"""Export utilities for receipts (PDF, CSV formatters)."""

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
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus import (
    Image as RLImage,
)

from app.receipt.models import Receipt

# Color palette - matches frontend grayscale theme (shadcn/ui)
_PRIMARY = colors.HexColor("#2d2d2d")  # --primary: oklch(0.205 0 0)
_TEXT_DARK = colors.HexColor("#1a1a1a")  # --foreground: oklch(0.145 0 0)
_TEXT_MUTED = colors.HexColor("#737373")  # --muted-foreground: oklch(0.556 0 0)
_BORDER = colors.HexColor("#e5e5e5")  # --border: oklch(0.922 0 0)
_SECONDARY_BG = colors.HexColor("#f5f5f5")  # --secondary: oklch(0.97 0 0)
_ROW_ALT = colors.HexColor("#fafafa")  # alternating row background


class ReceiptPDFGenerator:
    """Generator for creating professional PDF reports from receipt data."""

    def __init__(self) -> None:
        """Initialize the PDF generator."""
        self.buffer = BytesIO()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self) -> None:
        """Set up custom paragraph styles for the PDF."""
        self.styles.add(
            ParagraphStyle(
                name="ReportTitle",
                parent=self.styles["Heading1"],
                fontSize=22,
                textColor=_PRIMARY,
                spaceAfter=4,
                alignment=1,
                fontName="Helvetica-Bold",
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="Timestamp",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=_TEXT_MUTED,
                alignment=1,
                spaceAfter=8,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="SectionTitle",
                parent=self.styles["Heading2"],
                fontSize=11,
                textColor=_PRIMARY,
                spaceBefore=0,
                spaceAfter=6,
                fontName="Helvetica-Bold",
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="ReceiptHeader",
                parent=self.styles["Heading2"],
                fontSize=13,
                textColor=_PRIMARY,
                spaceBefore=12,
                spaceAfter=6,
                fontName="Helvetica-Bold",
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="SmallLabel",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=_TEXT_MUTED,
            )
        )

    def generate(self, receipts: list[Receipt], include_images: bool = False) -> bytes:
        """Generate a PDF report from a list of receipts."""
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            rightMargin=0.6 * inch,
            leftMargin=0.6 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        story: list = []

        # Header
        story.append(Paragraph("Receipt Report", self.styles["ReportTitle"]))
        timestamp = datetime.now().strftime("%B %d, %Y • %I:%M %p")
        story.append(Paragraph(timestamp, self.styles["Timestamp"]))
        story.append(
            HRFlowable(width="100%", thickness=1, color=_BORDER, spaceAfter=12)
        )

        # Summary section (side-by-side layout)
        story.extend(self._create_summary_section(receipts))

        # Each receipt
        for receipt in receipts:
            story.extend(
                self._create_receipt_section(receipt, include_images=include_images)
            )

        doc.build(story)
        pdf_bytes = self.buffer.getvalue()
        self.buffer.close()
        return pdf_bytes

    def _create_summary_section(self, receipts: list[Receipt]) -> list:
        """Create compact summary with stats and category breakdown side-by-side."""
        elements: list = []

        # Calculate statistics
        total_receipts = len(receipts)
        total_by_currency: dict[str, Decimal] = defaultdict(Decimal)
        # Track category totals by currency: {category: {currency: amount}}
        category_by_currency: dict[str, dict[str, Decimal]] = defaultdict(
            lambda: defaultdict(Decimal)
        )

        for receipt in receipts:
            total_by_currency[receipt.currency] += receipt.total_amount
            for item in receipt.items:
                cat_name = item.category.name if item.category else "Uncategorized"
                category_by_currency[cat_name][item.currency] += item.total_price

        # Build left column: Summary stats
        left_content = [[Paragraph("Summary", self.styles["SectionTitle"])]]
        left_content.append([self._stat_cell("Total Receipts", str(total_receipts))])
        for currency, amount in sorted(total_by_currency.items()):
            left_content.append(
                [self._stat_cell(f"Total ({currency})", f"{amount:.2f}")]
            )

        left_table = Table(left_content, colWidths=[2.8 * inch])
        left_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )

        # Build right column: Category breakdown as table with currency columns
        currencies = sorted(total_by_currency.keys())

        if category_by_currency and currencies:
            # Sort categories by total across all currencies
            def total_for_category(cat: str) -> Decimal:
                return sum(category_by_currency[cat].values())

            sorted_cats = sorted(
                category_by_currency.keys(), key=total_for_category, reverse=True
            )[:6]  # Top 6 categories

            # Build table: header row + data rows
            header = ["Category"] + currencies
            cat_table_data = [header]

            for cat in sorted_cats:
                row: list[str] = [cat]
                for curr in currencies:
                    amt = category_by_currency[cat].get(curr)
                    row.append(f"{amt:.2f}" if amt else "—")
                cat_table_data.append(row)

            # Calculate column widths: Category gets more space, currencies split rest
            cat_col_width = 2.0 * inch
            curr_col_width = (4.0 - 2.0) / max(len(currencies), 1) * inch
            col_widths = [cat_col_width] + [curr_col_width] * len(currencies)

            right_table = Table(cat_table_data, colWidths=col_widths)
            right_table.setStyle(
                TableStyle(
                    [
                        # Header row
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("TEXTCOLOR", (0, 0), (-1, 0), _PRIMARY),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                        # Data rows
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 9),
                        ("TEXTCOLOR", (0, 1), (-1, -1), _TEXT_DARK),
                        # Alignment
                        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                        ("ALIGN", (0, 0), (0, -1), "LEFT"),
                        # Padding
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                )
            )
        else:
            # No categories - empty placeholder
            right_table = Table([[""]], colWidths=[4 * inch])

        # Combine into two-column layout
        main_table = Table(
            [[left_table, right_table]],
            colWidths=[3 * inch, 4 * inch],
        )
        main_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        # Wrap in a box (7.3" = full content width)
        box_table = Table(
            [[main_table]],
            colWidths=[7.3 * inch],
        )
        box_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), _SECONDARY_BG),
                    ("BOX", (0, 0), (-1, -1), 1, _BORDER),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )

        elements.append(box_table)
        elements.append(Spacer(1, 0.15 * inch))

        return elements

    def _stat_cell(self, label: str, value: str) -> Table:
        """Create a compact stat display."""
        data = [
            [
                Paragraph(
                    f"<font size='8' color='#737373'>{label}</font>",
                    self.styles["Normal"],
                ),
                Paragraph(
                    f"<font size='11'><b>{value}</b></font>", self.styles["Normal"]
                ),
            ]
        ]
        t = Table(data, colWidths=[1.4 * inch, 1.2 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]
            )
        )
        return t

    def _create_receipt_section(
        self, receipt: Receipt, include_images: bool = False
    ) -> list:
        """Create a compact section for a single receipt."""
        elements: list = []

        # Receipt header with inline details
        header_text = f"{receipt.store_name}"
        elements.append(Paragraph(header_text, self.styles["ReceiptHeader"]))

        # Compact details line
        date_str = receipt.purchase_date.strftime("%b %d, %Y")
        details_parts = [
            f"<b>{date_str}</b>",
            f"<b>{receipt.currency} {receipt.total_amount:.2f}</b>",
        ]
        if receipt.payment_method:
            method = receipt.payment_method.value.replace("_", " ").title()
            details_parts.append(method)

        details_line = " &nbsp;•&nbsp; ".join(details_parts)
        elements.append(
            Paragraph(
                f"<font size='9' color='#737373'>{details_line}</font>",
                self.styles["Normal"],
            )
        )
        elements.append(Spacer(1, 6))

        # Items table - compact with repeating header
        items_data: list[list[str]] = [["Item", "Category", "Qty", "Price", "Total"]]
        for item in receipt.items:
            cat_name = item.category.name if item.category else "—"
            items_data.append(
                [
                    item.name,
                    cat_name,
                    str(item.quantity),
                    f"{item.unit_price:.2f}",
                    f"{item.total_price:.2f}",
                ]
            )

        # Full width table (7.3" = page width minus margins)
        # Distribute: Item 3.4", Category 1.6", Qty 0.5", Price 0.9", Total 0.9"
        items_table = Table(
            items_data,
            colWidths=[3.4 * inch, 1.6 * inch, 0.5 * inch, 0.9 * inch, 0.9 * inch],
            repeatRows=1,
        )
        items_table.setStyle(
            TableStyle(
                [
                    # Header row
                    ("BACKGROUND", (0, 0), (-1, 0), _PRIMARY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    # Data rows
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("TEXTCOLOR", (0, 1), (-1, -1), _TEXT_DARK),
                    # Alignment
                    ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                    ("ALIGN", (0, 0), (1, -1), "LEFT"),
                    # Grid and padding
                    ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    # Alternating rows
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, _ROW_ALT],
                    ),
                ]
            )
        )

        elements.append(items_table)

        # Receipt image (inline, if requested)
        if include_images and receipt.image_path:
            img_elements = self._create_image_section(receipt.image_path)
            if img_elements:
                elements.append(Spacer(1, 8))
                elements.extend(img_elements)

        elements.append(Spacer(1, 0.15 * inch))
        elements.append(
            HRFlowable(
                width="100%",
                thickness=0.5,
                color=_BORDER,
                spaceBefore=0,
                spaceAfter=8,
            )
        )

        return elements

    def _create_image_section(self, image_path: str) -> list:
        """Create receipt image section."""
        elements: list = []
        path = Path(image_path)

        if not path.exists():
            return elements

        try:
            pil_image = PILImage.open(path)

            # Scale to fit - max 5 inches wide, 6 inches tall
            max_w, max_h = 5 * inch, 6 * inch
            w_ratio = max_w / pil_image.width
            h_ratio = max_h / pil_image.height
            scale = min(w_ratio, h_ratio, 1.0)  # Don't upscale

            new_w = pil_image.width * scale
            new_h = pil_image.height * scale

            elements.append(
                Paragraph(
                    "<font size='8' color='#737373'>Receipt Image</font>",
                    self.styles["Normal"],
                )
            )
            elements.append(Spacer(1, 4))

            img = RLImage(str(path), width=new_w, height=new_h)
            # Keep image with its label
            elements = [KeepTogether(elements + [img])]

        except Exception:  # noqa: S110 - intentionally silent; missing image shouldn't break PDF
            return []

        return elements

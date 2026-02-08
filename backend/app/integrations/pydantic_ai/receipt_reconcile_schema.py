from typing import Literal

from pydantic import BaseModel, Field


class ReceiptItemAdjustment(BaseModel):
    """Suggested adjustment for a receipt item."""

    item_id: int = Field(description="ID of the existing item to adjust")
    remove: Literal[True] = Field(
        default=True,
        description=(
            "Remove this item from the receipt when it looks like a duplicate or OCR noise"
        ),
    )
    reason: str | None = Field(
        default=None,
        description="Brief reason for removing this item (1 short sentence)",
        max_length=180,
    )


class ReceiptReconcileAnalysis(BaseModel):
    """AI reconciliation suggestions for a receipt."""

    adjustments: list[ReceiptItemAdjustment] = Field(
        description="List of existing items to remove"
    )

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import computed_field
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from ..category.models import Category


# Base model for receipt data
class ReceiptBase(SQLModel):
    """Base model for receipt data."""

    store_name: str = Field(index=True)
    total_amount: Decimal = Field(max_digits=10, decimal_places=2)
    currency: str = Field(
        description="Currency symbol for total amount (e.g., $, £, €)"
    )
    purchase_date: datetime = Field(default_factory=lambda: datetime.now(UTC))


# Receipt model for database
class Receipt(ReceiptBase, table=True):
    """Receipt model for database."""

    id: int | None = Field(default=None, primary_key=True)
    image_path: str = Field(unique=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    items: list["ReceiptItem"] = Relationship(
        back_populates="receipt",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


# Base model for receipt item data
class ReceiptItemBase(SQLModel):
    """Base model for receipt item data."""

    name: str = Field(index=True)
    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(max_digits=10, decimal_places=2)
    total_price: Decimal = Field(max_digits=10, decimal_places=2)
    currency: str = Field(description="Currency symbol (e.g., $, £, €)")
    category_id: int | None = Field(default=None, foreign_key="category.id")

    @computed_field
    @property
    def total_cost(self) -> Decimal:
        """Calculate the total cost as unit_price multiplied by quantity."""
        return self.unit_price * self.quantity


# Receipt item model for database
class ReceiptItem(ReceiptItemBase, table=True):
    """Receipt item model for database."""

    id: int | None = Field(default=None, primary_key=True)
    receipt_id: int = Field(foreign_key="receipt.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    receipt: Receipt = Relationship(back_populates="items")
    category: "Category" = Relationship(
        back_populates="items",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


# Request Schemas
class ReceiptCreate(ReceiptBase):
    """Schema for creating a receipt."""

    image_path: str


class ReceiptUpdate(SQLModel):
    """Schema for updating a receipt."""

    store_name: str | None = Field(default=None)
    total_amount: Decimal | None = Field(default=None)
    purchase_date: datetime | None = Field(default=None)
    notes: str | None = Field(default=None)
    currency: str | None = Field(default=None)


class ReceiptItemCreate(ReceiptItemBase):
    """Schema for creating a receipt item."""

    receipt_id: int


class ReceiptItemUpdate(SQLModel):
    """Schema for updating a receipt item."""

    name: str | None = Field(default=None)
    quantity: int | None = Field(default=None, ge=1)
    unit_price: Decimal | None = Field(default=None)
    total_price: Decimal | None = Field(default=None)
    currency: str | None = Field(default=None)
    category_id: int | None = Field(default=None)


# Response Schemas
class ReceiptItemRead(ReceiptItemBase):
    """Schema for reading a receipt item."""

    id: int
    receipt_id: int
    created_at: datetime
    updated_at: datetime


class ReceiptRead(ReceiptBase):
    """Schema for reading a receipt."""

    id: int
    image_path: str
    created_at: datetime
    updated_at: datetime
    items: list[ReceiptItemRead]

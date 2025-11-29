from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import computed_field
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel._compat import SQLModelConfig

if TYPE_CHECKING:
    from ..category.models import Category


# Base model for receipt data
class ReceiptBase(SQLModel):
    """Base model for receipt data."""

    store_name: str = Field(
        index=True,
        max_length=255,
        description="Name of the store where the purchase was made",
    )
    total_amount: Decimal = Field(
        max_digits=10, decimal_places=2, description="Total amount of the purchase"
    )
    currency: str = Field(
        description="Currency symbol for total amount (e.g., $, £, €)"
    )
    purchase_date: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Date of purchase"
    )
    image_path: str = Field(
        unique=True, description="Path to the image file of the receipt"
    )


# Receipt model for database
class Receipt(ReceiptBase, table=True):
    """Receipt model for database."""

    id: int | None = Field(
        default=None, primary_key=True, description="Unique identifier for the receipt"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Date and time the receipt was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Date and time the receipt was last updated",
    )

    # Relationships
    items: list["ReceiptItem"] = Relationship(
        back_populates="receipt",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


# Base model for receipt item data
class ReceiptItemBase(SQLModel):
    """Base model for receipt item data."""

    name: str = Field(index=True, max_length=255, description="Name of the item")
    quantity: int = Field(ge=1, description="Quantity of the item")
    unit_price: Decimal = Field(
        max_digits=10, decimal_places=2, description="Unit price of the item"
    )
    total_price: Decimal = Field(
        max_digits=10, decimal_places=2, description="Total price of the item"
    )
    currency: str = Field(description="Currency symbol (e.g., $, £, €)")
    category_id: int | None = Field(
        default=None,
        foreign_key="category.id",
        description="ID of the category the item belongs to",
    )
    receipt_id: int = Field(
        foreign_key="receipt.id", description="ID of the receipt the item belongs to"
    )

    @computed_field
    @property
    def total_cost(self) -> Decimal:
        """Calculate the total cost as unit_price multiplied by quantity."""
        return self.unit_price * self.quantity


# Receipt item model for database
class ReceiptItem(ReceiptItemBase, table=True):
    """Receipt item model for database."""

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Date and time the item was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Date and time the item was last updated",
    )

    # Relationships
    receipt: Receipt = Relationship(back_populates="items")
    category: "Category" = Relationship(
        back_populates="items",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


# Request Schemas
class ReceiptCreate(ReceiptBase):
    """Schema for creating a receipt."""

    pass


class ReceiptUpdate(SQLModel):
    """Schema for updating a receipt.

    All fields are optional to allow partial updates.
    """

    store_name: str | None = Field(
        default=None,
        max_length=255,
        description="Name of the store where the purchase was made",
    )
    total_amount: Decimal | None = Field(
        default=None,
        max_digits=10,
        decimal_places=2,
        description="Total amount of the purchase",
    )
    currency: str | None = Field(
        default=None, description="Currency symbol (e.g., $, £, €)"
    )
    purchase_date: datetime | None = Field(default=None, description="Date of purchase")


class ReceiptItemCreate(ReceiptItemBase):
    """Schema for creating a receipt item."""

    pass


class ReceiptItemUpdate(SQLModel):
    """Schema for updating a receipt item.

    All fields are optional to allow partial updates.
    """

    name: str | None = Field(
        default=None, max_length=255, description="Name of the item"
    )
    quantity: int | None = Field(default=None, ge=1, description="Quantity of the item")
    unit_price: Decimal | None = Field(
        default=None,
        max_digits=10,
        decimal_places=2,
        description="Unit price of the item",
    )
    total_price: Decimal | None = Field(
        default=None,
        max_digits=10,
        decimal_places=2,
        description="Total price of the item",
    )
    currency: str | None = Field(
        default=None, description="Currency symbol (e.g., $, £, €)"
    )
    category_id: int | None = Field(
        default=None,
        foreign_key="category.id",
        description="ID of the category the item belongs to",
    )


# Response Schemas
class ReceiptItemRead(ReceiptItemBase):
    """Schema for reading a receipt item."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = SQLModelConfig(from_attributes=True)


class ReceiptRead(ReceiptBase):
    """Schema for reading a receipt."""

    id: int
    created_at: datetime
    updated_at: datetime
    items: list[ReceiptItemRead]

    model_config = SQLModelConfig(from_attributes=True)

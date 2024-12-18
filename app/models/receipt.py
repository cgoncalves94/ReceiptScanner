from datetime import UTC, datetime
from typing import Any

from pydantic import ConfigDict, computed_field
from sqlmodel import Field, Relationship, SQLModel

from .category import Category, CategoryRead


# Base Models
class ReceiptItemBase(SQLModel):
    """Base model defining core attributes for a receipt item."""

    name: str = Field(min_length=1, max_length=255)
    price: float = Field(ge=0)
    quantity: float = Field(default=1.0, ge=0)
    currency: str = Field(max_length=10)


class ReceiptBase(SQLModel):
    """Base model containing essential receipt information."""

    store_name: str = Field(min_length=1, max_length=255, index=True)
    total_amount: float = Field(ge=0)
    currency: str = Field(max_length=10)
    image_path: str
    date: datetime | None


# Database Models
class ReceiptItem(ReceiptItemBase, table=True):
    """Database model for storing individual items within a receipt."""

    id: int | None = Field(default=None, primary_key=True)
    receipt_id: int = Field(foreign_key="receipt.id", ondelete="CASCADE")
    category_id: int | None = Field(
        default=None, foreign_key="category.id", ondelete="SET NULL"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    receipt: "Receipt" = Relationship(back_populates="items")
    category: Category | None = Relationship(back_populates="items")


class Receipt(ReceiptBase, table=True):
    """Database model for storing complete receipt records with associated items."""

    id: int | None = Field(default=None, primary_key=True)
    processed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    items: list[ReceiptItem] = Relationship(
        back_populates="receipt",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


# Request Schemas
class ReceiptItemCreate(ReceiptItemBase):
    """Schema for creating new receipt items with optional receipt and category associations."""

    receipt_id: int | None
    category_id: int | None


class ReceiptCreate(SQLModel):
    """Schema for initial receipt creation with minimal required fields."""

    store_name: str | None
    total_amount: float | None
    currency: str
    image_path: str
    date: datetime | None


class ReceiptUpdate(SQLModel):
    """Schema for partial updates to existing receipt records."""

    store_name: str | None = None
    total_amount: float | None = None
    currency: str | None = None
    date: datetime | None = None
    processed: bool | None = None


# Response Schemas
class ReceiptItemRead(ReceiptItemBase):
    """Schema for API responses containing receipt item details with category information."""

    id: int
    receipt_id: int
    category: CategoryRead | None
    category_id: int | None

    model_config = ConfigDict(from_attributes=True)


class ReceiptRead(ReceiptBase):
    """Schema for API responses containing complete receipt information with items."""

    id: int
    processed: bool = False
    items: list[ReceiptItemRead]

    model_config = ConfigDict(from_attributes=True)


class ReceiptsRead(SQLModel):
    """Schema for paginated list of receipts with total count."""

    data: list[ReceiptRead]
    count: int


class ReceiptItemsByCategory(SQLModel):
    """Schema for receipt items grouped by category with cost calculations."""

    id: int
    name: str
    price: float
    quantity: float
    currency: str
    category_id: int

    @computed_field
    @property
    def total_cost(self) -> float:
        """Calculate the total cost as price multiplied by quantity."""
        return self.price * self.quantity

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_aggregation(cls, item: Any, category_id: int) -> "ReceiptItemsByCategory":
        """Create an instance from database aggregation results."""
        return cls(
            id=item.id,
            name=item.name,
            price=item.total_price / item.quantity if item.quantity > 0 else 0,
            quantity=item.quantity,
            currency=item.currency,
            category_id=category_id,
        )

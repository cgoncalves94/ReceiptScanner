from datetime import UTC, datetime

from pydantic import ConfigDict, computed_field
from sqlmodel import Field, Relationship, SQLModel

from .category import Category, CategoryRead


# Base Models
class ReceiptItemBase(SQLModel):
    """Base model defining core attributes for a receipt item."""

    id: int | None = Field(default=None, primary_key=True, nullable=False)
    name: str = Field(min_length=1, max_length=255)
    price: float = Field(ge=0)
    quantity: float = Field(default=1.0, ge=0)
    currency: str = Field(max_length=10)


class ReceiptBase(SQLModel):
    """Base model containing essential receipt information."""

    id: int | None = Field(default=None, primary_key=True, nullable=False)
    store_name: str = Field(min_length=1, max_length=255, index=True)
    total_amount: float = Field(ge=0)
    currency: str = Field(max_length=10)
    image_path: str
    date: datetime | None


# Database Models
class ReceiptItem(ReceiptItemBase, table=True):
    """Database model for storing individual items within a receipt."""

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

    processed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    items: list[ReceiptItem] = Relationship(
        back_populates="receipt",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


# Request Schemas
class ReceiptItemCreate(SQLModel):
    """Schema for creating new receipt items with optional receipt and category associations."""

    name: str = Field(min_length=1, max_length=255)
    price: float = Field(ge=0)
    quantity: float = Field(default=1.0, ge=0)
    currency: str = Field(max_length=10)
    receipt_id: int | None = None
    category_id: int | None = None


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

    receipt_id: int
    category: CategoryRead | None
    category_id: int | None

    model_config = ConfigDict(from_attributes=True)


class ReceiptRead(ReceiptBase):
    """Schema for API responses containing receipt details."""

    processed: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReceiptWithItemsRead(ReceiptRead):
    """Schema for API responses containing complete receipt information with items."""

    items: list[ReceiptItemRead]


class ReceiptsRead(SQLModel):
    """Schema for paginated list of receipts with total count."""

    data: list[ReceiptWithItemsRead]
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
    def from_items(
        cls, items: list[ReceiptItem], category_id: int
    ) -> list["ReceiptItemsByCategory"]:
        """Create aggregated items from a list of receipt items."""
        # Group items by name
        grouped_items: dict[str, list[ReceiptItem]] = {}
        for item in items:
            if item.name not in grouped_items:
                grouped_items[item.name] = []
            grouped_items[item.name].append(item)

        # Create aggregated items
        result = []
        for name, group in grouped_items.items():
            total_quantity = sum(item.quantity for item in group)
            total_price = sum(item.price * item.quantity for item in group)

            result.append(
                cls(
                    id=group[0].id,  # Use first item's ID
                    name=name,
                    price=total_price / total_quantity if total_quantity > 0 else 0,
                    quantity=total_quantity,
                    currency=group[0].currency,  # Use first item's currency
                    category_id=category_id,
                )
            )

        return result

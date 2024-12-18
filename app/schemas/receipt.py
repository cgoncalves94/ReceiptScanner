from datetime import datetime
from typing import Any

from pydantic import BaseModel, computed_field

from .category import CategoryRead


class ReceiptItemBase(BaseModel):
    name: str
    price: float
    quantity: float = 1.0
    currency: str
    category_id: int | None


class ReceiptItemCreate(ReceiptItemBase):
    receipt_id: int | None


class ReceiptItemRead(ReceiptItemBase):
    id: int
    receipt_id: int
    category: CategoryRead | None

    class Config:
        from_attributes = True


class ReceiptItemsByCategory(BaseModel):
    """Item in category with computed values."""

    id: int
    name: str
    price: float
    quantity: float
    currency: str
    category_id: int

    @computed_field
    @property
    def total_cost(self) -> float:
        """Calculate total cost (price * quantity)."""
        return self.price * self.quantity

    class Config:
        from_attributes = True

    @classmethod
    def from_aggregation(cls, item: Any, category_id: int) -> "ReceiptItemsByCategory":
        """Create from aggregated database results."""
        return cls(
            id=item.id,
            name=item.name,
            price=item.total_price / item.quantity if item.quantity > 0 else 0,
            quantity=item.quantity,
            currency=item.currency,
            category_id=category_id,
        )


class ReceiptBase(BaseModel):
    store_name: str
    total_amount: float
    currency: str
    image_path: str
    date: datetime | None


class ReceiptCreate(BaseModel):
    store_name: str | None
    total_amount: float | None
    currency: str
    image_path: str
    date: datetime | None


class ReceiptUpdate(BaseModel):
    store_name: str | None = None
    total_amount: float | None = None
    currency: str | None = None
    date: datetime | None = None
    processed: bool | None = None

    class Config:
        from_attributes = True


class ReceiptRead(ReceiptBase):
    id: int
    processed: bool = False
    items: list[ReceiptItemRead]

    class Config:
        from_attributes = True


class ReceiptListResponse(BaseModel):
    """Simplified receipt response for listing."""

    id: int
    store_name: str
    total_amount: float
    currency: str
    date: datetime
    processed: bool

    class Config:
        from_attributes = True

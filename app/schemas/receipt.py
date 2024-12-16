from datetime import datetime

from pydantic import BaseModel

from ..models import Receipt as DBReceipt
from ..models import ReceiptItem as DBReceiptItem
from .category import Category


class ReceiptItemBase(BaseModel):
    name: str
    price: float
    quantity: float = 1.0
    category_id: int | None = None


class ReceiptItemCreate(ReceiptItemBase):
    pass


class ReceiptItem(ReceiptItemBase):
    id: int
    receipt_id: int
    category: Category | None = None

    class Config:
        from_attributes = True
        model = DBReceiptItem


class ReceiptBase(BaseModel):
    store_name: str
    total_amount: float
    image_path: str
    date: datetime | None = None


class ReceiptCreate(BaseModel):
    store_name: str | None = None  # Will be filled by AI
    total_amount: float | None = None  # Will be filled by AI
    image_path: str
    date: datetime | None = None  # Will be filled by AI with receipt's actual date


# Add this new class for updates
class ReceiptUpdate(BaseModel):
    store_name: str | None = None
    total_amount: float | None = None
    date: datetime | None = None
    processed: bool | None = None

    class Config:
        from_attributes = True
        model = DBReceipt


class Receipt(ReceiptBase):
    id: int
    processed: bool = False
    items: list[ReceiptItem]

    class Config:
        from_attributes = True
        model = DBReceipt


class ReceiptResponse(BaseModel):
    id: int
    store_name: str
    total_amount: float
    date: datetime
    items: list[ReceiptItem]

    class Config:
        from_attributes = True
        model = DBReceipt


class ReceiptListResponse(BaseModel):
    """Simplified receipt response for listing."""

    id: int
    store_name: str
    total_amount: float
    date: datetime
    processed: bool

    class Config:
        from_attributes = True
        model = DBReceipt

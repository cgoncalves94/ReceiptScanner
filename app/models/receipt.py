from datetime import datetime

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel


class Category(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    description: str | None = None
    items: list["ReceiptItem"] = Relationship(back_populates="category")


class ReceiptItem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    receipt_id: int = Field(foreign_key="receipt.id")
    name: str
    price: float
    quantity: float = 1.0
    category_id: int | None = Field(default=None, foreign_key="category.id")

    receipt: "Receipt" = Relationship(back_populates="items")
    category: Category | None = Relationship(back_populates="items")


class Receipt(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    store_name: str = Field(index=True)
    total_amount: float
    date: datetime
    image_path: str
    processed: bool = Field(default=False)

    items: list[ReceiptItem] = Relationship(back_populates="receipt")


class ReceiptCreate(BaseModel):
    store_name: str | None = None  # Will be filled by AI
    total_amount: float | None = None  # Will be filled by AI
    image_path: str
    date: datetime | None = None  # Will be filled by AI with receipt's actual date


class ReceiptResponse(BaseModel):
    id: int
    store_name: str
    total_amount: float
    date: datetime
    items: list[ReceiptItem]


class ReceiptListResponse(BaseModel):
    """Simplified receipt response for listing."""

    id: int
    store_name: str
    total_amount: float
    date: datetime
    processed: bool

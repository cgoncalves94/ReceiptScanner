from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from .category import Category


class ReceiptItem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    receipt_id: int = Field(foreign_key="receipt.id", ondelete="CASCADE")
    name: str
    price: float
    quantity: float = 1.0
    category_id: int | None = Field(
        default=None, foreign_key="category.id", ondelete="SET NULL"
    )

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

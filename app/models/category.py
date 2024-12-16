from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .receipt import ReceiptItem


class Category(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    description: str | None = None
    items: list["ReceiptItem"] = Relationship(back_populates="category")

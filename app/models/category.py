from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import ConfigDict
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .receipt import ReceiptItem


# Base Models
class CategoryBase(SQLModel):
    """Base model defining core attributes for a category."""

    name: str = Field(unique=True, index=True, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


# Database Models
class Category(CategoryBase, table=True):
    """Database model for storing categories with associated receipt items."""

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    items: list["ReceiptItem"] = Relationship(
        back_populates="category", sa_relationship_kwargs={"lazy": "selectin"}
    )


# Request Schemas
class CategoryCreate(CategoryBase):
    """Schema for creating new categories."""

    pass


class CategoryUpdate(SQLModel):
    """Schema for partial updates to existing categories."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


# Response Schemas
class CategoryRead(CategoryBase):
    """Schema for API responses containing category details."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoriesRead(SQLModel):
    """Schema for paginated list of categories with total count."""

    data: list[CategoryRead]
    count: int

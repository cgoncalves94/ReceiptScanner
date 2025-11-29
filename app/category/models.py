from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel
from sqlmodel._compat import SQLModelConfig

if TYPE_CHECKING:
    from ..receipt.models import ReceiptItem


# Database Model (also serves as base for responses)
class CategoryBase(SQLModel):
    """Base model for category data."""

    name: str = Field(
        unique=True,
        index=True,
        min_length=1,
        max_length=255,
        description="Name of the category",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Description of the category",
    )


class Category(CategoryBase, table=True):
    """Category model for database."""

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
        description="Unique identifier for the category",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Date and time the category was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Date and time the category was last updated",
    )

    # Relationships
    items: list["ReceiptItem"] = Relationship(
        back_populates="category",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


# Request Schemas
class CategoryCreate(CategoryBase):
    """Schema for creating a category."""

    pass


class CategoryUpdate(SQLModel):
    """Schema for updating a category."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Name of the category",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Description of the category",
    )


# Response Schemas
class CategoryRead(CategoryBase):
    """Schema for reading a category."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = SQLModelConfig(from_attributes=True)

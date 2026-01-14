from datetime import UTC, datetime

from sqlmodel import Field, SQLModel
from sqlmodel._compat import SQLModelConfig


# Database Model (also serves as base for responses)
class UserBase(SQLModel):
    """Base model for user data."""

    email: str = Field(
        unique=True,
        index=True,
        min_length=3,
        max_length=255,
        description="User email address",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the user account is active",
    )


class User(UserBase, table=True):
    """User model for database."""

    __tablename__ = "user"

    id: int | None = Field(
        default=None,
        primary_key=True,
        nullable=False,
        description="Unique identifier for the user",
    )
    hashed_password: str = Field(
        description="Hashed password for the user",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Date and time the user was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Date and time the user was last updated",
    )


# Request Schemas
class UserCreate(SQLModel):
    """Schema for creating a user."""

    email: str = Field(
        min_length=3,
        max_length=255,
        description="User email address",
    )
    password: str = Field(
        min_length=8,
        max_length=100,
        description="User password (plain text, will be hashed)",
    )


class UserUpdate(SQLModel):
    """Schema for updating a user."""

    email: str | None = Field(
        default=None,
        min_length=3,
        max_length=255,
        description="User email address",
    )
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=100,
        description="User password (plain text, will be hashed)",
    )
    is_active: bool | None = Field(
        default=None,
        description="Whether the user account is active",
    )


# Response Schemas
class UserRead(UserBase):
    """Schema for reading a user."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = SQLModelConfig(from_attributes=True)

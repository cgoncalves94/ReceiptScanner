"""initial database setup

Revision ID: 8af1e70d0a0f
Revises:
Create Date: 2025-03-05 17:54:05.892123

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8af1e70d0a0f"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create category table
    op.create_table(
        "category",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_category_name"), "category", ["name"], unique=True)

    # Create receipt table
    op.create_table(
        "receipt",
        sa.Column("store_name", sa.String(length=255), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("purchase_date", sa.DateTime(), nullable=False),
        sa.Column("image_path", sa.String(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("image_path"),
    )
    op.create_index(
        op.f("ix_receipt_store_name"), "receipt", ["store_name"], unique=False
    )

    # Create receiptitem table
    op.create_table(
        "receiptitem",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("total_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("receipt_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["category.id"]),
        sa.ForeignKeyConstraint(["receipt_id"], ["receipt.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_receiptitem_name"), "receiptitem", ["name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_receiptitem_name"), table_name="receiptitem")
    op.drop_table("receiptitem")
    op.drop_index(op.f("ix_receipt_store_name"), table_name="receipt")
    op.drop_table("receipt")
    op.drop_index(op.f("ix_category_name"), table_name="category")
    op.drop_table("category")

"""add user_id to models

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-14 14:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6g7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add user_id column to receipt table
    op.add_column(
        "receipt",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )
    op.create_index(op.f("ix_receipt_user_id"), "receipt", ["user_id"], unique=False)
    op.create_foreign_key(
        "fk_receipt_user_id_user",
        "receipt",
        "user",
        ["user_id"],
        ["id"],
    )

    # Add user_id column to category table
    op.add_column(
        "category",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f("ix_category_user_id"), "category", ["user_id"], unique=False
    )
    op.create_foreign_key(
        "fk_category_user_id_user",
        "category",
        "user",
        ["user_id"],
        ["id"],
    )


def downgrade() -> None:
    # Remove user_id from category table
    op.drop_constraint("fk_category_user_id_user", "category", type_="foreignkey")
    op.drop_index(op.f("ix_category_user_id"), table_name="category")
    op.drop_column("category", "user_id")

    # Remove user_id from receipt table
    op.drop_constraint("fk_receipt_user_id_user", "receipt", type_="foreignkey")
    op.drop_index(op.f("ix_receipt_user_id"), table_name="receipt")
    op.drop_column("receipt", "user_id")

"""add receipt metadata

Revision ID: cd15e3c2931a
Revises: 8af1e70d0a0f
Create Date: 2026-01-12 23:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "cd15e3c2931a"
down_revision: str | None = "8af1e70d0a0f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add notes column (varchar 1000, nullable)
    op.add_column(
        "receipt",
        sa.Column("notes", sa.String(length=1000), nullable=True),
    )

    # Add tags column (PostgreSQL ARRAY of strings)
    op.add_column(
        "receipt",
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
    )

    # Add payment_method column (varchar 50, nullable)
    op.add_column(
        "receipt",
        sa.Column("payment_method", sa.String(length=50), nullable=True),
    )

    # Add tax_amount column (numeric 10,2, nullable)
    op.add_column(
        "receipt",
        sa.Column("tax_amount", sa.Numeric(precision=10, scale=2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("receipt", "tax_amount")
    op.drop_column("receipt", "payment_method")
    op.drop_column("receipt", "tags")
    op.drop_column("receipt", "notes")

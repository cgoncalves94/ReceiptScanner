"""Central registry of all SQLModel models.

This module imports all models to ensure they are registered with SQLModel metadata.
Import this module in alembic env.py to ensure all models are available for migrations.
"""

from app.category.models import Category
from app.receipt.models import Receipt, ReceiptItem

__all__ = [
    "Category",
    "Receipt",
    "ReceiptItem",
]

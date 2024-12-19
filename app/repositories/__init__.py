"""Repository package initialization.

This package implements the repository pattern for database access.
Each repository handles database operations for a specific domain model.
"""

from .category import CategoryRepository
from .receipt import ReceiptRepository

__all__ = [
    "CategoryRepository",
    "ReceiptRepository",
]

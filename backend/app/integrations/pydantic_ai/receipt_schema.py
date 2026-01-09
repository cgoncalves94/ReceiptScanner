from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CurrencySymbol(str, Enum):
    """Currency symbols for standardization."""

    EURO = "€"
    DOLLAR = "$"
    POUND = "£"

    @classmethod
    def standardize(cls, value: str) -> str:
        """Standardize currency string to a symbol.

        Args:
            value: Currency string to standardize

        Returns:
            Standardized currency symbol
        """
        # Mapping of various currency formats to standard symbols
        mapping = {
            # Euro variations
            "EUR": cls.EURO,
            "EURO": cls.EURO,
            "EUROS": cls.EURO,
            "€": cls.EURO,
            # Dollar variations
            "USD": cls.DOLLAR,
            "DOLLAR": cls.DOLLAR,
            "DOLLARS": cls.DOLLAR,
            "$": cls.DOLLAR,
            # Pound variations
            "GBP": cls.POUND,
            "POUND": cls.POUND,
            "POUNDS": cls.POUND,
            "£": cls.POUND,
        }

        # Convert to uppercase for case-insensitive matching
        upper_value = value.upper().strip()

        # Return mapped symbol or original if not found
        return mapping.get(upper_value, value)


class Category(BaseModel):
    """Category information for receipt items."""

    name: str = Field(description="Name of the category")
    description: str = Field(description="Description of what belongs in this category")


class ReceiptItem(BaseModel):
    """Individual item from a receipt."""

    name: str = Field(description="Name of the item")
    price: float = Field(description="Price of the item", ge=0)
    quantity: float = Field(description="Quantity of the item", ge=0, default=1.0)
    currency: str = Field(description="Currency symbol (e.g., $, £, €)")
    category: Category = Field(description="Category information for the item")


class ReceiptAnalysis(BaseModel):
    """Complete receipt analysis result."""

    store_name: str = Field(description="Name of the store")
    total_amount: float = Field(description="Total amount of the receipt", ge=0)
    currency: str = Field(description="Currency symbol used in the receipt")
    date: datetime = Field(description="Date and time of the receipt")
    items: list[ReceiptItem] = Field(description="List of items on the receipt")

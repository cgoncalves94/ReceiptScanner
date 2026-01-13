from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CurrencyCode(str, Enum):
    """ISO 4217 currency codes for standardization."""

    EUR = "EUR"
    USD = "USD"
    GBP = "GBP"

    @classmethod
    def standardize(cls, value: str) -> str:
        """Standardize currency string to ISO 4217 code.

        Args:
            value: Currency string to standardize (symbol or code)

        Returns:
            Standardized ISO currency code (EUR, USD, GBP)
        """
        # Mapping of various currency formats to ISO codes
        mapping = {
            # Euro variations
            "EUR": cls.EUR,
            "EURO": cls.EUR,
            "EUROS": cls.EUR,
            "€": cls.EUR,
            # Dollar variations
            "USD": cls.USD,
            "DOLLAR": cls.USD,
            "DOLLARS": cls.USD,
            "$": cls.USD,
            # Pound variations
            "GBP": cls.GBP,
            "POUND": cls.GBP,
            "POUNDS": cls.GBP,
            "£": cls.GBP,
        }

        # Convert to uppercase for case-insensitive matching
        upper_value = value.upper().strip()

        # Return mapped ISO code or original if not found
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
    currency: str = Field(
        description="Currency code or symbol (e.g., USD, EUR, GBP, $, £, €)"
    )
    category: Category = Field(description="Category information for the item")


class ReceiptAnalysis(BaseModel):
    """Complete receipt analysis result."""

    store_name: str = Field(description="Name of the store")
    total_amount: float = Field(description="Total amount of the receipt", ge=0)
    currency: str = Field(description="Currency code or symbol used in the receipt")
    date: datetime = Field(description="Date and time of the receipt")
    items: list[ReceiptItem] = Field(description="List of items on the receipt")

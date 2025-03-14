"""Unit tests for the receipt schema module."""

from app.integrations.pydantic_ai.receipt_schema import CurrencySymbol


def test_currency_symbol_standardize_euro():
    """Test standardizing Euro currency formats."""
    # Test various Euro formats
    assert CurrencySymbol.standardize("EUR") == "€"
    assert CurrencySymbol.standardize("euro") == "€"
    assert CurrencySymbol.standardize("EUROS") == "€"
    assert CurrencySymbol.standardize("€") == "€"


def test_currency_symbol_standardize_dollar():
    """Test standardizing Dollar currency formats."""
    # Test various Dollar formats
    assert CurrencySymbol.standardize("USD") == "$"
    assert CurrencySymbol.standardize("dollar") == "$"
    assert CurrencySymbol.standardize("DOLLARS") == "$"
    assert CurrencySymbol.standardize("$") == "$"


def test_currency_symbol_standardize_pound():
    """Test standardizing Pound currency formats."""
    # Test various Pound formats
    assert CurrencySymbol.standardize("GBP") == "£"
    assert CurrencySymbol.standardize("pound") == "£"
    assert CurrencySymbol.standardize("POUNDS") == "£"
    assert CurrencySymbol.standardize("£") == "£"


def test_currency_symbol_standardize_unknown():
    """Test standardizing unknown currency formats."""
    # Test unknown format - should return original
    assert CurrencySymbol.standardize("XYZ") == "XYZ"
    assert CurrencySymbol.standardize("¥") == "¥"

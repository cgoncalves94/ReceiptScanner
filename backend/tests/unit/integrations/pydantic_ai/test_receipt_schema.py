"""Unit tests for the receipt schema module."""

from app.integrations.pydantic_ai.receipt_schema import CurrencyCode


def test_currency_code_standardize_euro():
    """Test standardizing Euro currency formats to ISO code."""
    # Test various Euro formats → EUR
    assert CurrencyCode.standardize("EUR") == "EUR"
    assert CurrencyCode.standardize("euro") == "EUR"
    assert CurrencyCode.standardize("EUROS") == "EUR"
    assert CurrencyCode.standardize("€") == "EUR"


def test_currency_code_standardize_dollar():
    """Test standardizing Dollar currency formats to ISO code."""
    # Test various Dollar formats → USD
    assert CurrencyCode.standardize("USD") == "USD"
    assert CurrencyCode.standardize("dollar") == "USD"
    assert CurrencyCode.standardize("DOLLARS") == "USD"
    assert CurrencyCode.standardize("$") == "USD"


def test_currency_code_standardize_pound():
    """Test standardizing Pound currency formats to ISO code."""
    # Test various Pound formats → GBP
    assert CurrencyCode.standardize("GBP") == "GBP"
    assert CurrencyCode.standardize("pound") == "GBP"
    assert CurrencyCode.standardize("POUNDS") == "GBP"
    assert CurrencyCode.standardize("£") == "GBP"


def test_currency_code_standardize_unknown():
    """Test standardizing unknown currency formats."""
    # Test unknown format - should return original
    assert CurrencyCode.standardize("XYZ") == "XYZ"
    assert CurrencyCode.standardize("¥") == "¥"

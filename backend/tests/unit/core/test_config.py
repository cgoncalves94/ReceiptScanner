"""Unit tests for the config module."""

import pytest

from app.core.config import Settings


def test_validate_api_keys_missing():
    """Test that validate_api_keys raises ValueError when GEMINI_API_KEY is not set."""
    # Arrange
    settings = Settings(GEMINI_API_KEY="")

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        settings.validate_api_keys()
    assert "GEMINI_API_KEY environment variable is not set" in str(exc_info.value)


def test_validate_api_keys_present():
    """Test that validate_api_keys does not raise an error when GEMINI_API_KEY is set."""
    # Arrange
    settings = Settings(GEMINI_API_KEY="test_key")

    # Act & Assert
    # Should not raise an exception
    settings.validate_api_keys()

"""Unit tests for authentication utilities."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import jwt
import pytest

from app.auth.utils import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password() -> None:
    """Test that password hashing works correctly."""
    # Arrange
    password = "mysecurepassword123"

    # Act
    hashed = hash_password(password)

    # Assert
    assert hashed != password
    assert isinstance(hashed, str)
    assert len(hashed) > 0
    # bcrypt hashes start with $2b$ or $2a$
    assert hashed.startswith("$2")


def test_hash_password_different_hashes() -> None:
    """Test that the same password produces different hashes (due to salt)."""
    # Arrange
    password = "mysecurepassword123"

    # Act
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    # Assert
    assert hash1 != hash2


def test_verify_password_correct() -> None:
    """Test password verification with correct password."""
    # Arrange
    password = "mysecurepassword123"
    hashed = hash_password(password)

    # Act
    result = verify_password(password, hashed)

    # Assert
    assert result is True


def test_verify_password_incorrect() -> None:
    """Test password verification with incorrect password."""
    # Arrange
    password = "mysecurepassword123"
    wrong_password = "wrongpassword"
    hashed = hash_password(password)

    # Act
    result = verify_password(wrong_password, hashed)

    # Assert
    assert result is False


def test_verify_password_empty() -> None:
    """Test password verification with empty password."""
    # Arrange
    password = "mysecurepassword123"
    hashed = hash_password(password)

    # Act
    result = verify_password("", hashed)

    # Assert
    assert result is False


@patch("app.auth.utils.settings")
def test_create_access_token_default_expiration(mock_settings: MagicMock) -> None:
    """Test creating an access token with default expiration."""
    # Arrange
    mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    mock_settings.JWT_SECRET_KEY = "test-secret-key"
    mock_settings.JWT_ALGORITHM = "HS256"
    data = {"sub": "user@example.com", "user_id": 1}

    # Act
    token = create_access_token(data)

    # Assert
    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify contents
    decoded = jwt.decode(
        token, mock_settings.JWT_SECRET_KEY, algorithms=[mock_settings.JWT_ALGORITHM]
    )
    assert decoded["sub"] == data["sub"]
    assert decoded["user_id"] == data["user_id"]
    assert "exp" in decoded


@patch("app.auth.utils.settings")
def test_create_access_token_custom_expiration(mock_settings: MagicMock) -> None:
    """Test creating an access token with custom expiration."""
    # Arrange
    mock_settings.JWT_SECRET_KEY = "test-secret-key"
    mock_settings.JWT_ALGORITHM = "HS256"
    data = {"sub": "user@example.com"}
    expires_delta = timedelta(minutes=15)

    # Act
    token = create_access_token(data, expires_delta=expires_delta)

    # Assert
    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify expiration is approximately correct
    decoded = jwt.decode(
        token, mock_settings.JWT_SECRET_KEY, algorithms=[mock_settings.JWT_ALGORITHM]
    )
    exp_time = datetime.fromtimestamp(decoded["exp"], tz=UTC)
    expected_exp = datetime.now(UTC) + expires_delta

    # Allow 5 second tolerance for test execution time
    assert abs((exp_time - expected_exp).total_seconds()) < 5


@patch("app.auth.utils.settings")
def test_create_access_token_preserves_data(mock_settings: MagicMock) -> None:
    """Test that create_access_token preserves all data fields."""
    # Arrange
    mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    mock_settings.JWT_SECRET_KEY = "test-secret-key"
    mock_settings.JWT_ALGORITHM = "HS256"
    data = {
        "sub": "user@example.com",
        "user_id": 1,
        "is_active": True,
        "custom_field": "custom_value",
    }

    # Act
    token = create_access_token(data)

    # Assert
    decoded = jwt.decode(
        token, mock_settings.JWT_SECRET_KEY, algorithms=[mock_settings.JWT_ALGORITHM]
    )
    assert decoded["sub"] == data["sub"]
    assert decoded["user_id"] == data["user_id"]
    assert decoded["is_active"] == data["is_active"]
    assert decoded["custom_field"] == data["custom_field"]


@patch("app.auth.utils.settings")
def test_decode_access_token_valid(mock_settings: MagicMock) -> None:
    """Test decoding a valid access token."""
    # Arrange
    mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    mock_settings.JWT_SECRET_KEY = "test-secret-key"
    mock_settings.JWT_ALGORITHM = "HS256"
    data = {"sub": "user@example.com", "user_id": 1}
    token = create_access_token(data)

    # Act
    decoded = decode_access_token(token)

    # Assert
    assert decoded["sub"] == data["sub"]
    assert decoded["user_id"] == data["user_id"]
    assert "exp" in decoded


@patch("app.auth.utils.settings")
def test_decode_access_token_expired(mock_settings: MagicMock) -> None:
    """Test decoding an expired access token."""
    # Arrange
    mock_settings.JWT_SECRET_KEY = "test-secret-key"
    mock_settings.JWT_ALGORITHM = "HS256"
    data = {"sub": "user@example.com"}
    # Create token that expired 1 minute ago
    expired_token = create_access_token(data, expires_delta=timedelta(minutes=-1))

    # Act & Assert
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired_token)


@patch("app.auth.utils.settings")
def test_decode_access_token_invalid_signature(mock_settings: MagicMock) -> None:
    """Test decoding a token with invalid signature."""
    # Arrange
    mock_settings.JWT_SECRET_KEY = "test-secret-key"
    mock_settings.JWT_ALGORITHM = "HS256"
    # Create token with different secret
    data = {"sub": "user@example.com"}
    token = jwt.encode(data, "wrong-secret-key", algorithm="HS256")

    # Act & Assert
    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(token)


@patch("app.auth.utils.settings")
def test_decode_access_token_malformed(mock_settings: MagicMock) -> None:
    """Test decoding a malformed token."""
    # Arrange
    mock_settings.JWT_SECRET_KEY = "test-secret-key"
    mock_settings.JWT_ALGORITHM = "HS256"
    malformed_token = "this.is.not.a.valid.jwt"

    # Act & Assert
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(malformed_token)


@patch("app.auth.utils.settings")
def test_decode_access_token_empty(mock_settings: MagicMock) -> None:
    """Test decoding an empty token."""
    # Arrange
    mock_settings.JWT_SECRET_KEY = "test-secret-key"
    mock_settings.JWT_ALGORITHM = "HS256"

    # Act & Assert
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("")

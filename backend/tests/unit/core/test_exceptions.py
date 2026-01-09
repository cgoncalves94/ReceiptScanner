"""Unit tests for the exceptions module."""

from app.core.exceptions import (
    AppError,
    BadRequestError,
    ConflictError,
    DatabaseError,
    InternalServerError,
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
)


def test_app_error():
    """Test the base AppError exception."""
    # Test with default values
    error = AppError()
    assert error.detail == "An error occurred"
    assert error.code == "APP_ERROR"

    # Test with custom values
    custom_error = AppError(detail="Custom error", code="CUSTOM_CODE")
    assert custom_error.detail == "Custom error"
    assert custom_error.code == "CUSTOM_CODE"


def test_validation_error():
    """Test the ValidationError exception."""
    # Test with default values
    error = ValidationError()
    assert error.detail == "Invalid data provided"
    assert error.code == "VALIDATION_ERROR"

    # Test with custom values
    custom_error = ValidationError(
        detail="Custom validation error", code="CUSTOM_VALIDATION"
    )
    assert custom_error.detail == "Custom validation error"
    assert custom_error.code == "CUSTOM_VALIDATION"


def test_service_unavailable_error():
    """Test the ServiceUnavailableError exception."""
    # Test with default values
    error = ServiceUnavailableError()
    assert error.detail == "Service is currently unavailable"
    assert error.code == "SERVICE_UNAVAILABLE"

    # Test with custom values
    custom_error = ServiceUnavailableError(
        detail="Custom service error", code="CUSTOM_SERVICE"
    )
    assert custom_error.detail == "Custom service error"
    assert custom_error.code == "CUSTOM_SERVICE"


def test_not_found_error():
    """Test the NotFoundError exception."""
    # Test with default values
    error = NotFoundError()
    assert error.detail == "Resource not found"
    assert error.code == "NOT_FOUND"

    # Test with custom values
    custom_error = NotFoundError(
        detail="Custom not found error", code="CUSTOM_NOT_FOUND"
    )
    assert custom_error.detail == "Custom not found error"
    assert custom_error.code == "CUSTOM_NOT_FOUND"


def test_conflict_error():
    """Test the ConflictError exception."""
    # Test with default values
    error = ConflictError()
    assert error.detail == "Resource already exists"
    assert error.code == "CONFLICT"

    # Test with custom values
    custom_error = ConflictError(detail="Custom conflict error", code="CUSTOM_CONFLICT")
    assert custom_error.detail == "Custom conflict error"
    assert custom_error.code == "CUSTOM_CONFLICT"


def test_bad_request_error():
    """Test the BadRequestError exception."""
    # Test with default values
    error = BadRequestError()
    assert error.detail == "Invalid request"
    assert error.code == "BAD_REQUEST"

    # Test with custom values
    custom_error = BadRequestError(
        detail="Custom bad request error", code="CUSTOM_BAD_REQUEST"
    )
    assert custom_error.detail == "Custom bad request error"
    assert custom_error.code == "CUSTOM_BAD_REQUEST"


def test_database_error():
    """Test the DatabaseError exception."""
    # Test with default values
    error = DatabaseError()
    assert error.detail == "Database operation failed"
    assert error.code == "DATABASE_ERROR"

    # Test with custom values
    custom_error = DatabaseError(detail="Custom database error", code="CUSTOM_DATABASE")
    assert custom_error.detail == "Custom database error"
    assert custom_error.code == "CUSTOM_DATABASE"


def test_internal_server_error():
    """Test the InternalServerError exception."""
    # Test with default values
    error = InternalServerError()
    assert error.detail == "An unexpected internal error occurred"
    assert error.code == "INTERNAL_ERROR"

    # Test with custom values
    custom_error = InternalServerError(
        detail="Custom internal error", code="CUSTOM_INTERNAL"
    )
    assert custom_error.detail == "Custom internal error"
    assert custom_error.code == "CUSTOM_INTERNAL"

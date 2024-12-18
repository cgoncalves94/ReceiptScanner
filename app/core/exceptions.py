from enum import Enum

from fastapi import status


class ErrorCode(Enum):
    """Error codes for domain exceptions."""

    # Domain errors
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    INVALID_INPUT = "INVALID_INPUT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"

    # Database errors
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_CONSTRAINT_ERROR = "DATABASE_CONSTRAINT_ERROR"
    DATABASE_NOT_AVAILABLE = "DATABASE_NOT_AVAILABLE"


class DomainException(Exception):
    """Base exception for domain errors."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DatabaseConnectionError(DomainException):
    """Raised when database connection fails."""

    def __init__(self, message: str = "Database connection failed"):
        super().__init__(
            code=ErrorCode.DATABASE_CONNECTION_ERROR,
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

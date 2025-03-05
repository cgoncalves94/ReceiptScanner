from typing import Any

from fastapi import HTTPException, status


class UnprocessableEntityError(HTTPException):
    """Raised when validation fails."""

    def __init__(self, detail: str | dict[str, Any]) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
        )


class ServiceUnavailableError(HTTPException):
    """Raised when an external API request fails."""

    def __init__(self, detail: str | dict[str, Any]) -> None:
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)


class NotFoundError(HTTPException):
    """Raised when a requested resource is not found."""

    def __init__(self, detail: str | dict[str, Any]) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictError(HTTPException):
    """Raised when attempting to create a resource that already exists."""

    def __init__(self, detail: str | dict[str, Any]) -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class InternalServerError(HTTPException):
    """Raised when a database operation fails or other server-side errors occur."""

    def __init__(self, detail: str | dict[str, Any]) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )

    def __str__(self) -> str:
        """Override string representation to avoid status code prefix."""
        return str(self.detail)

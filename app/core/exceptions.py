from fastapi import HTTPException, status


class ValidationError(HTTPException):
    """Raised when data validation fails."""

    def __init__(self, errors: list[dict[str, str]] | dict[str, str]):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"validation_errors": errors},
        )


class ImageProcessingError(HTTPException):
    """Raised when image processing fails."""

    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ExternalAPIError(HTTPException):
    """Raised when external API calls fail."""

    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)


class ResourceNotFoundError(HTTPException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, resource_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with ID {resource_id} not found",
        )


class ResourceAlreadyExistsError(HTTPException):
    """Raised when attempting to create a resource that already exists."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{resource} with {identifier} already exists",
        )


class DatabaseError(HTTPException):
    """Raised when a database operation fails."""

    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

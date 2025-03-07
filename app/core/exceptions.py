# Base application exception
class AppError(Exception):
    """Base exception for all application errors."""

    def __init__(self, detail: str = "An error occurred", code: str = "APP_ERROR"):
        super().__init__(detail)
        self.detail = detail
        self.code = code


# Business domain exceptions
class ValidationError(AppError):
    """Raised when data validation fails."""

    def __init__(
        self, detail: str = "Invalid data provided", code: str = "VALIDATION_ERROR"
    ):
        super().__init__(detail=detail, code=code)


class ServiceUnavailableError(AppError):
    """Raised when an external API request fails."""

    def __init__(
        self,
        detail: str = "Service is currently unavailable",
        code: str = "SERVICE_UNAVAILABLE",
    ):
        super().__init__(detail=detail, code=code)


class NotFoundError(AppError):
    """Raised when a requested resource is not found."""

    def __init__(self, detail: str = "Resource not found", code: str = "NOT_FOUND"):
        super().__init__(detail=detail, code=code)


class ConflictError(AppError):
    """Raised when attempting to create a resource that already exists."""

    def __init__(self, detail: str = "Resource already exists", code: str = "CONFLICT"):
        super().__init__(detail=detail, code=code)


class BadRequestError(AppError):
    """Raised when a request is invalid."""

    def __init__(self, detail: str = "Invalid request", code: str = "BAD_REQUEST"):
        super().__init__(detail=detail, code=code)


class DatabaseError(AppError):
    """Raised when a database operation fails."""

    def __init__(
        self, detail: str = "Database operation failed", code: str = "DATABASE_ERROR"
    ):
        super().__init__(detail=detail, code=code)


class InternalServerError(AppError):
    """Raised for unexpected internal errors."""

    def __init__(
        self,
        detail: str = "An unexpected internal error occurred",
        code: str = "INTERNAL_ERROR",
    ):
        super().__init__(detail=detail, code=code)

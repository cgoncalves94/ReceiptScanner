import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from app.core.exceptions import (
    ConflictError,
    InternalServerError,
    NotFoundError,
    ServiceUnavailableError,
    UnprocessableEntityError,
)

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle HTTP exceptions with unified error handling."""
    # Map HTTP status codes to our custom exceptions
    status_to_exception = {
        status.HTTP_400_BAD_REQUEST: HTTPException,
        status.HTTP_404_NOT_FOUND: NotFoundError,
        status.HTTP_409_CONFLICT: ConflictError,
        status.HTTP_422_UNPROCESSABLE_ENTITY: UnprocessableEntityError,
        status.HTTP_500_INTERNAL_SERVER_ERROR: InternalServerError,
        status.HTTP_503_SERVICE_UNAVAILABLE: ServiceUnavailableError,
    }

    # Handle FastAPI's built-in HTTPException by converting to our custom exceptions
    if (
        isinstance(exc, HTTPException) and exc.__class__ == HTTPException
    ):  # Only convert if it's the base class
        # Get the appropriate exception class or use HTTPException as fallback
        exception_class = status_to_exception.get(exc.status_code, HTTPException)

        # If we have a custom exception for this status, use it
        if exception_class != HTTPException:
            # Create our custom exception with the same details
            custom_exc = exception_class(detail=exc.detail)
            # Use the custom exception instead
            exc = custom_exc

    # Log the error with request context
    log_message = f"HTTP {getattr(exc, 'status_code', 500)} error on {request.url.path}"
    if hasattr(exc, "detail"):
        log_message += f": {exc.detail}"
    logger.error(log_message)

    # Return the appropriate response
    return JSONResponse(
        status_code=getattr(exc, "status_code", 500),
        content={"detail": str(getattr(exc, "detail", str(exc)))},
    )


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle request validation errors."""
    if not isinstance(exc, RequestValidationError):
        return await unhandled_exception_handler(request, exc)

    errors = exc.errors()
    error_messages = []

    for error in errors:
        error_location = " -> ".join(str(loc) for loc in error["loc"])
        error_messages.append(f"{error_location}: {error['msg']}")

    # Log with request context
    logger.warning(f"Validation error on {request.url.path}: {error_messages}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": error_messages},
    )


async def database_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle database errors."""
    if not isinstance(exc, SQLAlchemyError):
        return await unhandled_exception_handler(request, exc)

    # Log with request context
    logger.error(f"Database error on {request.url.path}: {str(exc)}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error occurred"},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle any unhandled exceptions as a last resort."""
    # Log with full traceback for unexpected errors
    logger.exception(f"Unhandled exception on {request.url.path}: {str(exc)}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred"},
    )

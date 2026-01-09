import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import DataError, IntegrityError, OperationalError, SQLAlchemyError

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

logger = logging.getLogger(__name__)

# Map business exceptions to HTTP status codes
STATUS_CODE_MAPPING: dict[type[AppError], int] = {
    ValidationError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    ServiceUnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    InternalServerError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    BadRequestError: status.HTTP_400_BAD_REQUEST,
}


async def app_exception_handler(_: Request, exc: AppError) -> Response | JSONResponse:
    """Handle all application-specific exceptions."""
    # Get the appropriate status code based on exception class
    exception_class = exc.__class__
    status_code = STATUS_CODE_MAPPING.get(
        exception_class, status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    # Log the error with appropriate level
    logger.debug(f"app_exception_handler handling exception type: {type(exc).__name__}")

    # Standard FastAPI error format
    return JSONResponse(status_code=status_code, content={"detail": exc.detail})


async def validation_exception_handler(
    _: Request, exc: Exception
) -> Response | JSONResponse:
    """Handle validation exceptions from FastAPI and Pydantic."""
    if isinstance(exc, RequestValidationError):
        error_details = [
            f"Field '{' -> '.join(str(loc) for loc in error['loc'][1:])}' {error['msg']}"
            for error in exc.errors()
        ]
        # Log detailed validation errors
        logger.info(f"Request validation error: {error_details}")
        logger.info(f"Invalid data: {exc.body}")
    elif isinstance(exc, PydanticValidationError):
        error_details = [
            f"Field '{' -> '.join(str(loc) for loc in error['loc'])}' {error['msg']}"
            for error in exc.errors()
        ]
        logger.info(f"Pydantic validation error: {error_details}")
    else:
        error_details = ["Unknown validation error occurred."]
        logger.warning(f"Unknown validation error: {str(exc)}")

    error = ValidationError(detail="; ".join(error_details))
    return await app_exception_handler(_, error)


async def database_exception_handler(
    _: Request, exc: Exception
) -> Response | JSONResponse:
    """Handle database and connection-related exceptions with smart categorization."""
    # Extract original exception if available
    orig_exc = getattr(exc, "orig", exc)
    exc_type = type(orig_exc).__name__
    error_msg = str(orig_exc)

    # Log the error
    logger.error(f"Database error: {exc_type} - {error_msg}", exc_info=True)

    # Create appropriate business exception based on the error
    error: AppError
    if isinstance(exc, IntegrityError) or "unique" in error_msg.lower():
        error = ConflictError(detail="Resource already exists")
    elif "foreign key" in error_msg.lower():
        error = ValidationError(detail="Referenced resource not found")
    elif isinstance(exc, DataError) or "invalid input" in error_msg.lower():
        error = ValidationError(detail="Invalid data format or value provided")
    elif (
        isinstance(exc, ConnectionRefusedError | ConnectionError | OperationalError)
        or "connection" in error_msg.lower()
    ):
        error = DatabaseError(detail="Database is currently unavailable")
    else:
        # Generic database error
        error = DatabaseError(detail=f"A database error occurred: {error_msg}")

    return await app_exception_handler(_, error)


async def unhandled_exception_handler(
    _: Request, exc: Exception
) -> Response | JSONResponse:
    """Fallback handler for all other unhandled exceptions."""
    logger.error(f"Unhandled exception: {type(exc).__name__} - {exc}", exc_info=True)
    error = InternalServerError(detail="An unexpected internal error occurred")
    return await app_exception_handler(_, error)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register exception handlers for the FastAPI application.
    This follows the elegant approach from your main project.
    """
    # Business exceptions
    for exc_class in STATUS_CODE_MAPPING.keys():
        app.exception_handler(exc_class)(app_exception_handler)

    # Database exceptions
    app.exception_handler(SQLAlchemyError)(database_exception_handler)

    # Network/connection errors that might occur during database operations
    connection_errors = [
        ConnectionRefusedError,
        ConnectionError,
        ConnectionAbortedError,
        ConnectionResetError,
        TimeoutError,
    ]

    for error_type in connection_errors:
        app.exception_handler(error_type)(database_exception_handler)

    # Validation exceptions
    app.exception_handler(RequestValidationError)(validation_exception_handler)
    app.exception_handler(PydanticValidationError)(validation_exception_handler)

    # Fallback handler for unhandled exceptions
    app.exception_handler(Exception)(unhandled_exception_handler)

import logging
import sys

from fastapi import Request, status
from fastapi.responses import JSONResponse
from psycopg import errors
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


async def http_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Handle FastAPI's HTTPException and general exceptions with clean error messages."""
    # Handle HTTPExceptions (including our custom exceptions)
    if isinstance(exc, HTTPException):
        # For startup errors, suppress the traceback
        if isinstance(exc, DatabaseError):
            sys.tracebacklimit = 0

        # Clean up any status code prefix from the message
        detail = str(exc.detail)
        if str(exc.status_code) in detail:
            detail = detail.split(":", 1)[-1].strip()

        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": detail},
        )

    # Handle any unhandled exceptions
    error_msg = f"{exc.__class__.__name__}: {str(exc)}"
    logger.error(f"Unhandled error: {error_msg}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


async def sqlalchemy_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Handle SQLAlchemy errors with appropriate status codes."""
    if not isinstance(exc, SQLAlchemyError):
        return await http_exception_handler(_, exc)

    # Get the root cause of the error and log it for debugging
    root_error = getattr(exc, "orig", exc)
    logger.error(f"Database error: {str(root_error)}")

    # Handle specific PostgreSQL errors with clean user messages
    if isinstance(root_error, errors.OperationalError):
        if "Connection refused" in str(root_error):
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "detail": "Database connection failed. Please ensure PostgreSQL is running on port 5432"
                },
            )
        raise DatabaseError("Database unavailable")
    elif isinstance(root_error, errors.NumericValueOutOfRange):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": "ID value is too large. Maximum allowed value is 2,147,483,647"
            },
        )
    elif isinstance(root_error, errors.ForeignKeyViolation):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Referenced resource not found"},
        )
    elif isinstance(root_error, errors.UniqueViolation):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Resource already exists"},
        )

    # Default internal error
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error occurred"},
    )

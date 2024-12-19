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
    """Handle FastAPI's HTTPException with clean error messages."""
    if not isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    # Suppress traceback for startup errors
    if exc.status_code == 503 and "Database" in str(exc.detail):
        sys.tracebacklimit = 0
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def sqlalchemy_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Handle SQLAlchemy errors with appropriate status codes."""
    if not isinstance(exc, SQLAlchemyError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    # Get the root cause of the error
    root_error = getattr(exc, "orig", exc)
    error_msg = str(root_error).split("\n")[0]  # Get only the first line of the error

    # Handle specific PostgreSQL errors
    if isinstance(root_error, errors.OperationalError):
        if "Connection refused" in str(root_error):
            error_msg = "Database connection failed. Please ensure PostgreSQL is running on port 5432."
            logger.error(error_msg)
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": error_msg},
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
    logger.error(f"Database error: {error_msg}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error occurred"},
    )


async def general_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Handle any unhandled exceptions."""
    error_msg = f"{exc.__class__.__name__}: {str(exc)}"
    logger.error(f"Unhandled error: {error_msg}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )

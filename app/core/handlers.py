import logging
from http import HTTPStatus

from fastapi import status
from fastapi.responses import JSONResponse
from psycopg import errors
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import DatabaseConnectionError, DomainException, ErrorCode

logger = logging.getLogger(__name__)


async def domain_exception_handler(_, exc: DomainException) -> JSONResponse:
    """Handle domain exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "code": exc.code.value,
        },
    )


async def sqlalchemy_exception_handler(_, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy errors with appropriate status codes."""
    logger.error(f"Database error: {exc}")

    # Get the original database error
    if hasattr(exc, "orig"):
        # Handle specific PostgreSQL errors
        if isinstance(exc.orig, errors.NumericValueOutOfRange):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": f"{HTTPStatus(status.HTTP_400_BAD_REQUEST).phrase}: Value out of range",
                    "code": ErrorCode.DATABASE_CONSTRAINT_ERROR.value,
                },
            )
        elif isinstance(exc.orig, errors.ForeignKeyViolation):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": f"{HTTPStatus(status.HTTP_400_BAD_REQUEST).phrase}: Referenced resource not found",
                    "code": ErrorCode.DATABASE_CONSTRAINT_ERROR.value,
                },
            )
        elif isinstance(exc.orig, errors.UniqueViolation):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "detail": f"{HTTPStatus(status.HTTP_409_CONFLICT).phrase}: Resource already exists",
                    "code": ErrorCode.DATABASE_CONSTRAINT_ERROR.value,
                },
            )
        elif isinstance(exc.orig, errors.OperationalError):
            # Convert to DatabaseConnectionError for operational errors
            raise DatabaseConnectionError(
                f"{HTTPStatus(status.HTTP_503_SERVICE_UNAVAILABLE).phrase}: Database unavailable"
            )

    # Default internal error
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"{HTTPStatus(status.HTTP_500_INTERNAL_SERVER_ERROR).phrase}: Database error",
            "code": ErrorCode.DATABASE_CONNECTION_ERROR.value,
        },
    )

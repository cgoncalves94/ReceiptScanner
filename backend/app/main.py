import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import logfire
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app import __author__
from app.analytics.router import router as analytics_router
from app.auth.router import router as auth_router
from app.category.router import router as category_router
from app.core.config import settings
from app.core.db import check_db_connection, engine, init_db
from app.core.error_handlers import (
    register_exception_handlers,
)
from app.receipt.router import router as receipt_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifecycle manager."""
    try:
        logger.info(
            f"Starting {settings.PROJECT_NAME} v{settings.VERSION} by {__author__}"
        )
        await init_db()
        yield
    except SQLAlchemyError as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        # Clean shutdown
        await engine.dispose()
        logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
    description="Receipt Scanner API for analyzing receipts using computer vision",
    contact={"name": __author__},
)

# Only configure Logfire if not in test environment or if token is set
if settings.ENVIRONMENT.lower() != "test":  # pragma: no cover
    logfire.configure(
        token=settings.LOGFIRE_TOKEN,
        send_to_logfire=True,
        scrubbing=False,
        service_name="receipt-scanner",
    )
    logfire.instrument_fastapi(app)


# Register exception handlers
register_exception_handlers(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=[str(origin).rstrip("/") for origin in settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include domain routers
app.include_router(auth_router)
app.include_router(receipt_router)
app.include_router(category_router)
app.include_router(analytics_router)


# Define the root endpoint
@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """
    Root endpoint of the FastAPI application.
    Returns a welcome message.
    """
    return {"message": f"Welcome to the {settings.PROJECT_NAME}!"}


# Define the healthcheck endpoint
@app.get("/healthcheck", include_in_schema=False)
async def healthcheck() -> JSONResponse:
    """Health check endpoint that includes database status"""
    is_db_connected = await check_db_connection()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "database": "connected" if is_db_connected else "disconnected",
        },
    )

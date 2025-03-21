import logging
from contextlib import asynccontextmanager

import logfire
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app import __author__
from app.api.v1.router import APIRouter
from app.core.config import settings
from app.core.db import check_db_connection, engine, init_db
from app.core.error_handlers import (
    register_exception_handlers,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
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
    CORSMiddleware,  # type: ignore
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(APIRouter, prefix=settings.API_V1_STR)


# Define the root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint of the FastAPI application.
    Returns a welcome message.
    """
    return {"message": "Welcome to the Warestack Core API!"}


# Define the healthcheck endpoint
@app.get("/healthcheck", include_in_schema=False)
async def healthcheck():
    """Health check endpoint that includes database status"""
    is_db_connected = await check_db_connection()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "database": "connected" if is_db_connected else "disconnected",
        },
    )

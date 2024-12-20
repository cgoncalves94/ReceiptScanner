import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import __author__
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.db import engine, init_db
from app.core.exceptions import DatabaseError
from app.middlewares.error_handler import (
    http_exception_handler,
    sqlalchemy_exception_handler,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifecycle manager."""
    try:
        logger.info(
            f"Starting {settings.PROJECT_NAME} v{settings.VERSION} by {__author__}"
        )
        try:
            await init_db()
        except DatabaseError as e:
            # Suppress traceback for startup errors
            sys.tracebacklimit = 0
            # Pass through the original error without wrapping
            raise e
        yield
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

# Add exception handlers
app.add_exception_handler(Exception, http_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
        await conn.commit()
    return {"status": "healthy", "database": "connected"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.PROJECT_NAME,
        "status": "ok",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs",
        "openapi_url": f"{settings.API_V1_STR}/openapi.json",
        "health_check": "/health",
        "description": "Receipt Scanner API for analyzing receipts using computer vision",
        "author": __author__,
    }

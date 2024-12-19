import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from app import __author__
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.db import engine, init_db
from app.core.exceptions import DatabaseError
from app.middlewares.error_handler import (
    general_exception_handler,
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
        logger.info("Initializing database...")
        try:
            await init_db()
            logger.info("Database initialized successfully")
        except (SQLAlchemyError, DatabaseError):
            # Suppress traceback
            sys.tracebacklimit = 0
            error_msg = "Could not connect to the database. Please ensure PostgreSQL is running on port 5432."
            logger.error(error_msg)
            # Exit cleanly with just the error message
            raise HTTPException(status_code=503, detail=error_msg) from None
        yield
    finally:
        logger.info("Shutting down database connections...")
        await engine.dispose()
        logger.info("Database connections closed")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
    description="Receipt Scanner API for analyzing receipts using computer vision",
    contact={"name": __author__},
)

# Add exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

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

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import engine, init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifecycle manager."""
    try:
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

    yield

    # Cleanup (if needed)
    logger.info("Application shutdown")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

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
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return {"status": "healthy"}
    except SQLAlchemyError as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "detail": "Database connection failed"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Receipt Scanner API is running",
        "docs_url": "/docs",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }

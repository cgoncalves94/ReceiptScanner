"""Central router that aggregates all features-specific routers."""

from fastapi import APIRouter

from app.features.category.router import router as category_router
from app.features.receipt.router import router as receipt_router

# Create the main router
APIRouter = APIRouter()

# Include features routers
APIRouter.include_router(category_router)
APIRouter.include_router(receipt_router)

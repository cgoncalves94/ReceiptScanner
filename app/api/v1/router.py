"""Central router that aggregates all domains-specific routers."""

from fastapi import APIRouter

from app.domains.category.router import router as category_router
from app.domains.receipt.router import router as receipt_router

# Create the main router
APIRouter = APIRouter()

# Include domains routers
APIRouter.include_router(category_router)
APIRouter.include_router(receipt_router)

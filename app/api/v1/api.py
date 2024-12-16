from fastapi import APIRouter

from app.api.v1.endpoints import categories, receipts

api_router = APIRouter()
api_router.include_router(receipts.router, prefix="/receipts", tags=["receipts"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])

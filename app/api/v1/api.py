from fastapi import APIRouter

from app.api.v1.endpoints import receipts

api_router = APIRouter()
api_router.include_router(receipts.router, prefix="/receipts", tags=["receipts"])

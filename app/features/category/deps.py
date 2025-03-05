from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.deps import get_session

from .service import CategoryService


async def get_category_service(session: AsyncSession = Depends(get_session)):
    """Get a CategoryService instance with database session."""
    return CategoryService(session)


CategoryDeps = Annotated[CategoryService, Depends(get_category_service)]

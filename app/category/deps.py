from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.deps import get_session

from .services import CategoryService


async def get_category_service(
    session: AsyncSession = Depends(get_session),
) -> CategoryService:
    """Get an instance of the category service."""
    return CategoryService(session=session)


CategoryDeps = Annotated[CategoryService, Depends(get_category_service)]

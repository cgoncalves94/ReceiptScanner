from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.deps import get_session

from .repositories import CategoryRepository
from .services import CategoryService


async def get_category_repository(
    session: AsyncSession = Depends(get_session),
) -> CategoryRepository:
    """Get an instance of the category repository."""
    return CategoryRepository(session)


async def get_category_service(
    category_repo: CategoryRepository = Depends(get_category_repository),
) -> CategoryService:
    """Get an instance of the category service."""
    return CategoryService(
        session=category_repo.session, category_repository=category_repo
    )


CategoryDeps = Annotated[CategoryService, Depends(get_category_service)]

from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.deps import get_session

from .services import AnalyticsService


async def get_analytics_service(
    session: AsyncSession = Depends(get_session),
) -> AnalyticsService:
    """Get an instance of the analytics service."""
    return AnalyticsService(session=session)


AnalyticsDeps = Annotated[AnalyticsService, Depends(get_analytics_service)]

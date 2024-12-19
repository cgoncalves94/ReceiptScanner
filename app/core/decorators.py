import functools
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel.ext.asyncio.session import AsyncSession

logger = logging.getLogger(__name__)

T = TypeVar("T")


def transactional(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle database transactions.

    Usage:
        @transactional
        async def my_service_method(self, ...):
            # Method will be wrapped in a transaction
            ...
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        if not hasattr(args[0], "session") or not isinstance(
            args[0].session, AsyncSession
        ):
            raise ValueError("Transactional decorator requires 'session' attribute")

        try:
            async with args[0].session.begin_nested():
                return await func(*args, **kwargs)
        except SQLAlchemyError:
            # Let SQLAlchemy errors propagate for consistent handling
            raise

    return wrapper

import functools
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def transactional(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle database transactions.
    This decorator is specifically designed for methods of a service class
    that have been instantiated with a session.

    Usage:
        @transactional
        async def my_service_method(self, ...):
            # Method will be wrapped in a nested transaction
            ...
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        if not args:
            logger.error(f"No instance provided to {func.__name__}")
            raise ValueError(
                "Transactional decorator requires an instance as first argument"
            )

        # Get instance from args (typically 'self')
        instance = args[0]
        # Try to get session from instance
        session = getattr(instance, "session", None)

        if session is None or not hasattr(session, "begin_nested"):
            # Execute the function without transaction
            logger.warning(
                f"No valid session found for {func.__name__}, executing without transaction"
            )
            return await func(*args, **kwargs)

        # Execute with transaction
        try:
            async with session.begin_nested():
                result = await func(*args, **kwargs)
                return result
        except SQLAlchemyError as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            raise
        except Exception as e:
            logger.exception(f"Error in {func.__name__}: {str(e)}")
            raise

    return wrapper

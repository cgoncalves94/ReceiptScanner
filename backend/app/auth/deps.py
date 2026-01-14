"""Dependencies for authentication and authorization."""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.deps import get_session

from .models import User
from .services import AuthService
from .utils import decode_access_token

# HTTPBearer security scheme for extracting JWT tokens
security = HTTPBearer()


async def get_auth_service(
    session: AsyncSession = Depends(get_session),
) -> AuthService:
    """Get an instance of the auth service."""
    return AuthService(session=session)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: AuthService = Depends(get_auth_service),
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Authorization credentials containing the JWT token
        service: Auth service for database operations

    Returns:
        Current authenticated user

    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    token = credentials.credentials

    try:
        # Decode the JWT token
        payload = decode_access_token(token)
        user_id_str: str | None = payload.get("sub")

        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Convert string ID back to int
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None

    except jwt.InvalidTokenError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

    # Get the user from the database
    try:
        user = await service.get_user_by_id(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# Type aliases for dependency injection
AuthDeps = Annotated[AuthService, Depends(get_auth_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]

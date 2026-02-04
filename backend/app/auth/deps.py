"""Dependencies for authentication and authorization."""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth.models import User
from app.auth.services import AuthService
from app.auth.utils import decode_access_token
from app.core.deps import get_session
from app.core.exceptions import NotFoundError

# HTTPBearer security scheme for extracting JWT tokens
security = HTTPBearer()
TOKEN_COOKIE_KEY = "receipt_scanner_token"  # noqa: S105


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _inactive() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User account is inactive",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def _get_user_from_token(token: str, service: AuthService) -> User:
    try:
        # Decode the JWT token
        payload = decode_access_token(token)
        user_id_str: str | None = payload.get("sub")

        if user_id_str is None:
            raise _unauthorized()

        # Convert string ID back to int
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise _unauthorized() from None

    except jwt.InvalidTokenError as err:
        raise _unauthorized() from err

    # Get the user from the database
    try:
        user = await service.get_user_by_id(user_id)
    except NotFoundError:
        raise _unauthorized() from None

    if not user.is_active:
        raise _inactive()

    return user


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
    return await _get_user_from_token(credentials.credentials, service)


async def get_current_user_from_request(
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> User:
    """Get current user from Authorization header or auth cookie."""
    token: str | None = None

    auth_header = request.headers.get("Authorization")
    if auth_header:
        scheme, _, param = auth_header.partition(" ")
        if scheme.lower() == "bearer" and param:
            token = param
        else:
            token = None

    if not token:
        token = request.cookies.get(TOKEN_COOKIE_KEY)

    if not token:
        raise _unauthorized()

    return await _get_user_from_token(token, service)


# Type aliases for dependency injection
AuthDeps = Annotated[AuthService, Depends(get_auth_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserFromRequest = Annotated[User, Depends(get_current_user_from_request)]


def require_user_id(user: User) -> int:
    """Return a non-null user ID or raise if authentication is invalid."""
    if user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user.id

from fastapi import APIRouter, status

from app.auth.deps import AuthDeps, CurrentUser
from app.auth.models import User, UserCreate, UserRead
from app.auth.utils import create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    service: AuthDeps,
) -> User:
    """Register a new user."""
    return await service.register_user(user_in)


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    user_in: UserCreate,
    service: AuthDeps,
) -> dict[str, str]:
    """
    Authenticate a user and return an access token.

    Returns:
        Dictionary containing access_token and token_type
    """
    user = await service.authenticate_user(user_in.email, user_in.password)

    # Create JWT token (sub must be string per JWT spec)
    access_token = create_access_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserRead, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: CurrentUser,
) -> User:
    """Get the current authenticated user."""
    return current_user

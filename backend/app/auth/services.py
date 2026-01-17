"""Service for managing user authentication and user accounts."""

from datetime import UTC, datetime

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth.models import User, UserCreate, UserUpdate
from app.auth.utils import hash_password, verify_password
from app.core.exceptions import ConflictError, NotFoundError


class AuthService:
    """Service for managing users and authentication."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def register_user(self, user_in: UserCreate) -> User:
        """
        Register a new user.

        Args:
            user_in: User creation data with email and plain password

        Returns:
            Created user instance

        Raises:
            ConflictError: If user with email already exists
        """
        # Check if user already exists
        existing = await self.get_user_by_email(user_in.email)
        if existing:
            raise ConflictError(f"User with email '{user_in.email}' already exists")

        # Hash the password
        hashed_password = hash_password(user_in.password)

        # Create new user
        user = User(
            email=user_in.email,
            hashed_password=hashed_password,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def authenticate_user(self, email: str, password: str) -> User:
        """
        Authenticate a user by email and password.

        Args:
            email: User email address
            password: Plain text password

        Returns:
            Authenticated user instance

        Raises:
            NotFoundError: If credentials are invalid
        """
        user = await self.get_user_by_email(email)
        if not user:
            raise NotFoundError("Invalid email or password")

        if not verify_password(password, user.hashed_password):
            raise NotFoundError("Invalid email or password")

        if not user.is_active:
            raise NotFoundError("User account is inactive")

        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Get a user by email address.

        Args:
            email: User email address

        Returns:
            User instance if found, None otherwise
        """
        stmt = select(User).where(User.email == email)
        result: User | None = await self.session.scalar(stmt)
        return result

    async def get_user_by_id(self, user_id: int) -> User:
        """
        Get a user by ID.

        Args:
            user_id: User ID

        Returns:
            User instance

        Raises:
            NotFoundError: If user not found
        """
        stmt = select(User).where(User.id == user_id)
        user = await self.session.scalar(stmt)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
        return user

    async def update_user(self, user_id: int, user_in: UserUpdate) -> User:
        """
        Update a user.

        Args:
            user_id: User ID to update
            user_in: User update data

        Returns:
            Updated user instance

        Raises:
            NotFoundError: If user not found
            ConflictError: If email update conflicts with existing user
        """
        # Get the user
        user = await self.get_user_by_id(user_id)

        # If email is being updated, check for uniqueness
        if user_in.email is not None and user_in.email != user.email:
            existing = await self.get_user_by_email(user_in.email)
            if existing:
                raise ConflictError(f"User with email '{user_in.email}' already exists")

        # Prepare update data
        update_data = user_in.model_dump(exclude_unset=True, exclude={"id", "password"})

        # If password is being updated, hash it
        if user_in.password is not None:
            update_data["hashed_password"] = hash_password(user_in.password)

        # Update the user
        user.sqlmodel_update(update_data)
        user.updated_at = datetime.now(UTC)
        await self.session.flush()
        return user

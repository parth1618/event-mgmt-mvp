"""Authentication service for user registration and login."""

from datetime import timedelta
from uuid import UUID

from fastapi import HTTPException
from jose import JWTError
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_refresh_token,
    verify_token,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import Token, UserCreate


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        """Initialize auth service.

        Args:
            db: Database session.
        """
        self.db = db
        self.user_repo = UserRepository(db)

    async def register_user(self, user_data: UserCreate) -> User:
        """Register new user.

        Args:
            user_data: User registration data.

        Returns:
            User: Created user instance.

        Raises:
            HTTPException: If email already exists.
        """
        # Check if email exists
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(400, "Email already registered")

        # Create user
        user = await self.user_repo.create(
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            is_active=True,
            is_verified=False,  # Will be verified via email in production
        )

        logger.info(f"User registered: {user.email}")

        # Send welcome email
        if settings.EMAIL_ENABLED:
            from app.services.email_service import email_service

            await email_service.send_welcome_email(user.email, user.first_name or "User")

        return user

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """Authenticate user credentials.

        Args:
            email: User email.
            password: Plain text password.

        Returns:
            User | None: User if authenticated, None otherwise.
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        return user

    async def login(self, email: str, password: str) -> Token:
        """Login user and generate tokens.

        Args:
            email: User email.
            password: Plain text password.

        Returns:
            Token: Access and refresh tokens.

        Raises:
            HTTPException: If credentials are invalid.
        """
        user = await self.authenticate_user(email, password)
        if not user:
            raise HTTPException(401, "Incorrect email or password")

        # Generate tokens
        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        logger.info(f"User logged in: {user.email}")

        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    async def refresh_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token.

        Returns:
            Token: New access and refresh tokens.

        Raises:
            HTTPException: If refresh token is invalid.
        """
        try:
            # Use sync version - it's designed to work in async context via thread pool
            payload = verify_refresh_token(refresh_token)
            user_id_str: str = payload.get("sub")
            if user_id_str is None:
                raise HTTPException(401, "Invalid refresh token")

            user_id = UUID(user_id_str)
        except (JWTError, ValueError) as e:
            logger.warning(f"Invalid refresh token: {str(e)}")
            raise HTTPException(401, "Invalid refresh token")

        user = await self.user_repo.get(user_id)
        if not user or not user.is_active:
            raise HTTPException(401, "Inactive user or not found")

        # Generate new tokens
        access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    async def request_password_reset(self, email: str) -> None:
        """Request password reset token.

        Args:
            email: User email address.
        """
        user = await self.user_repo.get_by_email(email)

        # Don't reveal if email exists for security
        if not user:
            logger.info(f"Password reset requested for non-existent email: {email}")
            return

        # Generate reset token (valid for 1 hour)
        reset_token = create_access_token(
            data={"sub": str(user.id), "type": "password_reset"},
            expires_delta=timedelta(hours=1),
        )

        # Send reset email
        if settings.EMAIL_ENABLED:
            from app.services.email_service import email_service

            await email_service.send_password_reset(user.email, reset_token)
        else:
            logger.info(f"Password reset token for {email}: {reset_token}")

        logger.info(f"Password reset requested for: {email}")

    async def reset_password(self, token: str, new_password: str) -> None:
        """Reset password using token.

        Args:
            token: Password reset token.
            new_password: New password.

        Raises:
            HTTPException: If token is invalid or expired.
        """
        try:
            payload = verify_token(token)
            token_type = payload.get("type")
            user_id_str = payload.get("sub")

            if token_type != "password_reset" or not user_id_str:
                raise HTTPException(400, "Invalid reset token")

            user_id = UUID(user_id_str)
        except (JWTError, ValueError):
            raise HTTPException(400, "Invalid or expired reset token")

        user = await self.user_repo.get(user_id)
        if not user:
            raise HTTPException(400, "Invalid reset token")

        # Update password
        hashed = hash_password(new_password)
        await self.user_repo.update(user_id, hashed_password=hashed)

        logger.info(f"Password reset successfully for user: {user.email}")

"""User management service."""

from uuid import UUID

from fastapi import HTTPException, UploadFile
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserUpdate
from app.services.storage_service import storage_service
from app.utils.constants import ALLOWED_IMAGE_MIMES


class UserService:
    """Service for user management operations."""

    def __init__(self, db: AsyncSession):
        """Initialize user service."""
        self.db = db
        self.user_repo = UserRepository(db)

    async def get_user(self, user_id: UUID) -> User:
        """Get user by ID.

        Args:
            user_id: User UUID.

        Returns:
            User: User instance.

        Raises:
            HTTPException: If user not found.
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise HTTPException(404, "User not found")
        return user

    async def update_user(
        self, user_id: UUID, user_data: UserUpdate, current_user_id: UUID
    ) -> User:
        """Update user profile.

        Args:
            user_id: User UUID to update.
            user_data: Update data.
            current_user_id: ID of user making request.

        Returns:
            User: Updated user instance.

        Raises:
            HTTPException: If not authorized or user not found.
        """
        # Check authorization
        if user_id != current_user_id:
            raise HTTPException(403, "Not authorized to update this user")

        user = await self.user_repo.get(user_id)
        if not user:
            raise HTTPException(404, "User not found")

        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        updated_user = await self.user_repo.update(user_id, **update_data)

        logger.info(f"User updated: {user.email}")
        return updated_user

    async def upload_avatar(self, user_id: UUID, file: UploadFile, current_user_id: UUID) -> User:
        """Upload user avatar.

        Args:
            user_id: User UUID.
            file: Avatar image file.
            current_user_id: ID of user making request.

        Returns:
            User: Updated user with new avatar URL.

        Raises:
            HTTPException: If not authorized or upload fails.
        """
        # Check authorization
        if user_id != current_user_id:
            raise HTTPException(403, "Not authorized")

        user = await self.user_repo.get(user_id)
        if not user:
            raise HTTPException(404, "User not found")

        # Delete old avatar if exists
        if user.avatar_url:
            await storage_service.delete_file(user.avatar_url)

        # Upload new avatar
        avatar_url = await storage_service.upload_file(
            file, folder="avatars", allowed_types=ALLOWED_IMAGE_MIMES
        )

        # Update user
        updated_user = await self.user_repo.update(user_id, avatar_url=avatar_url)

        logger.info(f"Avatar uploaded for user: {user.email}")
        return updated_user

    async def delete_user(self, user_id: UUID, current_user_id: UUID) -> bool:
        """Delete user account.

        Args:
            user_id: User UUID to delete.
            current_user_id: ID of user making request.

        Returns:
            bool: True if deleted successfully.

        Raises:
            HTTPException: If not authorized.
        """
        # Check authorization
        if user_id != current_user_id:
            raise HTTPException(403, "Not authorized")

        user = await self.user_repo.get(user_id)
        if not user:
            raise HTTPException(404, "User not found")

        # Soft delete - just deactivate
        await self.user_repo.update(user_id, is_active=False)

        logger.info(f"User deactivated: {user.email}")
        return True

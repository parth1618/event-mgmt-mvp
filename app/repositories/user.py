"""User repository with email lookups and existence checks."""

from sqlalchemy import func, select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model with email operations."""

    def __init__(self, db):
        """Initialize user repository.

        Args:
            db: Database session.
        """
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email address.

        Args:
            email: User email address.

        Returns:
            User | None: User if found, None otherwise.
        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email.

        Args:
            email: User email address.

        Returns:
            bool: True if user exists, False otherwise.
        """
        result = await self.db.execute(
            select(func.count()).select_from(User).where(User.email == email)
        )
        count = result.scalar()
        return count > 0

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all active users.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records.

        Returns:
            list[User]: List of active users.
        """
        result = await self.db.execute(
            select(User)
            .where(User.is_active)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        return list(result.scalars().all())

"""User repository."""

from typing import Optional
from sqlalchemy import select
from app.models.user import User
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    """Repository for User model."""
    
    def __init__(self, db):
        super().__init__(User, db)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email.
        
        Args:
            email: User email.
            
        Returns:
            Optional[User]: User if found.
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email.
        
        Args:
            email: User email.
            
        Returns:
            bool: True if exists.
        """
        result = await self.db.execute(
            select(func.count()).select_from(User).where(User.email == email)
        )
        return result.scalar() > 0
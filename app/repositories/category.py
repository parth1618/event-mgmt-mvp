"""Category repository."""

from sqlalchemy import select

from app.models.category import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """Repository for Category model."""

    def __init__(self, db):
        super().__init__(Category, db)

    async def get_by_slug(self, slug: str) -> Category | None:
        """Get category by slug.

        Args:
            slug: Category slug.

        Returns:
            Category | None: Category if found.
        """
        result = await self.db.execute(select(Category).where(Category.slug == slug))
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Category]:
        """Get all active categories.

        Returns:
            list[Category]: Active categories.
        """
        result = await self.db.execute(
            select(Category).where(Category.is_active).order_by(Category.name.asc())
        )
        return list(result.scalars().all())

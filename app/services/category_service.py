"""Category management service."""

from uuid import UUID

from fastapi import HTTPException
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    """Service for category operations."""

    def __init__(self, db: AsyncSession):
        """Initialize category service."""
        self.db = db
        self.category_repo = CategoryRepository(db)

    async def list_categories(self, active_only: bool = True) -> list[Category]:
        """List all categories.

        Args:
            active_only: If True, return only active categories.

        Returns:
            list[Category]: List of categories.
        """
        if active_only:
            return await self.category_repo.list_active()
        return await self.category_repo.get_multi()

    async def get_category(self, category_id: UUID) -> Category:
        """Get category by ID.

        Args:
            category_id: Category UUID.

        Returns:
            Category: Category instance.

        Raises:
            HTTPException: If category not found.
        """
        category = await self.category_repo.get(category_id)
        if not category:
            raise HTTPException(404, "Category not found")
        return category

    async def create_category(
        self, category_data: CategoryCreate, current_user_role: str
    ) -> Category:
        """Create new category (admin only).

        Args:
            category_data: Category creation data.
            current_user_role: Role of user making request.

        Returns:
            Category: Created category.

        Raises:
            HTTPException: If not authorized or slug exists.
        """
        # Check authorization
        if current_user_role != "admin":
            raise HTTPException(403, "Admin access required")

        # Check if slug exists
        existing = await self.category_repo.get_by_slug(category_data.slug)
        if existing:
            raise HTTPException(400, "Category slug already exists")

        # Create category
        category = await self.category_repo.create(
            name=category_data.name,
            slug=category_data.slug,
            description=category_data.description,
            icon=category_data.icon,
            is_active=True,
        )

        logger.info(f"Category created: {category.name}")
        return category

    async def update_category(
        self, category_id: UUID, category_data: CategoryUpdate, current_user_role: str
    ) -> Category:
        """Update category (admin only).

        Args:
            category_id: Category UUID.
            category_data: Update data.
            current_user_role: Role of user making request.

        Returns:
            Category: Updated category.

        Raises:
            HTTPException: If not authorized or not found.
        """
        # Check authorization
        if current_user_role != "admin":
            raise HTTPException(403, "Admin access required")

        category = await self.category_repo.get(category_id)
        if not category:
            raise HTTPException(404, "Category not found")

        # Update category
        update_data = category_data.dict(exclude_unset=True)
        updated_category = await self.category_repo.update(category_id, **update_data)

        logger.info(f"Category updated: {category.name}")
        return updated_category

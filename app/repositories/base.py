"""Base repository with common CRUD operations."""

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)  # type: ignore


class BaseRepository(Generic[ModelType]):
    """Generic repository for CRUD operations."""

    def __init__(self, model: type[ModelType], db: AsyncSession):
        """Initialize repository.

        Args:
            model: SQLAlchemy model class.
            db: Database session.
        """
        self.model = model
        self.db = db

    async def create(self, **kwargs) -> ModelType:
        """Create new record.

        Args:
            **kwargs: Model field values.

        Returns:
            ModelType: Created instance.
        """
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def get(self, id: UUID) -> ModelType | None:
        """Get record by ID.

        Args:
            id: Record UUID.

        Returns:
            ModelType | None: Found instance or None.
        """
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self, skip: int = 0, limit: int = 100, order_by: str | None = None, **filters
    ) -> list[ModelType]:
        """Get multiple records with filters.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records.
            order_by: Field to order by.
            **filters: Field filters.

        Returns:
            list[ModelType]: List of instances.
        """
        query = select(self.model)

        # Apply filters
        for key, value in filters.items():
            if value is not None:
                query = query.where(getattr(self.model, key) == value)

        # Apply ordering
        if order_by:
            query = query.order_by(getattr(self.model, order_by))

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, id: UUID, **kwargs) -> ModelType | None:
        """Update record.

        Args:
            id: Record UUID.
            **kwargs: Fields to update.

        Returns:
            ModelType | None: Updated instance or None.
        """
        await self.db.execute(update(self.model).where(self.model.id == id).values(**kwargs))
        await self.db.commit()
        return await self.get(id)

    async def delete(self, id: UUID) -> bool:
        """Delete record.

        Args:
            id: Record UUID.

        Returns:
            bool: True if deleted, False otherwise.
        """
        result = await self.db.execute(delete(self.model).where(self.model.id == id))
        await self.db.commit()
        return result.rowcount > 0

    async def count(self, **filters) -> int:
        """Count records with filters.

        Args:
            **filters: Field filters.

        Returns:
            int: Count of matching records.
        """
        query = select(func.count()).select_from(self.model)
        for key, value in filters.items():
            if value is not None:
                query = query.where(getattr(self.model, key) == value)
        result = await self.db.execute(query)
        return result.scalar()

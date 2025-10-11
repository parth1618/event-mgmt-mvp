"""Order repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.order import Order
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    """Repository for Order model."""

    def __init__(self, db):
        super().__init__(Order, db)

    async def get_with_items(self, order_id: UUID) -> Order | None:
        """Get order with items loaded.

        Args:
            order_id: Order UUID.

        Returns:
            Order | None: Order with items.
        """
        result = await self.db.execute(
            select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 20) -> list[Order]:
        """Get orders by user.

        Args:
            user_id: User UUID.
            skip: Pagination offset.
            limit: Results limit.

        Returns:
            list[Order]: User orders.
        """
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.event))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_number(self, order_number: str) -> Order | None:
        """Get order by order number.

        Args:
            order_number: Order number.

        Returns:
            Order | None: Order if found.
        """
        result = await self.db.execute(select(Order).where(Order.order_number == order_number))
        return result.scalar_one_or_none()

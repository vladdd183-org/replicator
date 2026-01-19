"""Order module Unit of Work.

Manages transactions and domain events for order operations.
"""

from dataclasses import dataclass, field

from src.Containers.AppSection.OrderModule.Data.Repositories.OrderItemRepository import (
    OrderItemRepository,
)
from src.Containers.AppSection.OrderModule.Data.Repositories.OrderRepository import OrderRepository
from src.Ship.Parents.UnitOfWork import BaseUnitOfWork


@dataclass
class OrderUnitOfWork(BaseUnitOfWork):
    """Unit of Work for OrderModule.

    Provides transactional access to order repositories
    and domain event publishing.

    Attributes:
        orders: Repository for Order entities
        items: Repository for OrderItem entities

    Example:
        async with self.uow:
            order = Order(user_id=..., total_amount=...)
            await self.uow.orders.add(order)

            for item_data in items:
                item = OrderItem(order=order.id, ...)
                await self.uow.items.add(item)

            self.uow.add_event(OrderCreated(order_id=order.id, ...))
            await self.uow.commit()
    """

    orders: OrderRepository = field(default_factory=OrderRepository)
    items: OrderItemRepository = field(default_factory=OrderItemRepository)


__all__ = ["OrderUnitOfWork"]

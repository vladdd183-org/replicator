"""Order module Unit of Work.

Manages transactions and domain events for order operations.
"""

from dataclasses import dataclass

from src.Ship.Parents.UnitOfWork import BaseUnitOfWork
from src.Containers.AppSection.OrderModule.Data.Repositories.OrderRepository import OrderRepository
from src.Containers.AppSection.OrderModule.Data.Repositories.OrderItemRepository import OrderItemRepository


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
    
    orders: OrderRepository | None = None
    items: OrderItemRepository | None = None
    
    def __post_init__(self) -> None:
        """Initialize repositories if not provided."""
        if self.orders is None:
            self.orders = OrderRepository()
        if self.items is None:
            self.items = OrderItemRepository()


__all__ = ["OrderUnitOfWork"]

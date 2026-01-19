"""GetOrderQuery - Retrieve order by ID."""

from dataclasses import dataclass
from uuid import UUID

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.OrderModule.Data.Repositories.OrderRepository import OrderRepository
from src.Containers.AppSection.OrderModule.Data.Repositories.OrderItemRepository import OrderItemRepository
from src.Containers.AppSection.OrderModule.Models.Order import Order


@dataclass
class GetOrderInput:
    """Input for get order query."""
    
    order_id: UUID
    include_items: bool = True


@dataclass
class OrderWithItems:
    """Order with its items."""
    
    order: Order
    items: list


class GetOrderQuery(Query[GetOrderInput, OrderWithItems | None]):
    """Query: Get order by ID.
    
    Retrieves a single order with optional items.
    """
    
    def __init__(
        self,
        order_repository: OrderRepository,
        item_repository: OrderItemRepository,
    ) -> None:
        """Initialize query with dependencies.
        
        Args:
            order_repository: Repository for orders
            item_repository: Repository for order items
        """
        self.order_repository = order_repository
        self.item_repository = item_repository
    
    async def execute(self, input: GetOrderInput) -> OrderWithItems | None:
        """Execute the query.
        
        Args:
            input: GetOrderInput with order ID
            
        Returns:
            OrderWithItems if found, None otherwise
        """
        order = await self.order_repository.get(input.order_id)
        if order is None:
            return None
        
        items = []
        if input.include_items:
            items = await self.item_repository.get_by_order(input.order_id)
        
        return OrderWithItems(order=order, items=items)

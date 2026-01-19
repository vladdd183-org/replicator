"""GetOrderQuery - Retrieve order by ID.

CQRS Query: Read-only operation with direct ORM access.
Does NOT use Repository — optimized for performance.
"""

from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.OrderModule.Models.Order import Order
from src.Containers.AppSection.OrderModule.Models.OrderItem import OrderItem


class GetOrderInput(BaseModel):
    """Input for get order query.
    
    Uses frozen Pydantic model for immutability.
    """
    
    model_config = ConfigDict(frozen=True)
    
    order_id: UUID
    include_items: bool = True


@dataclass(frozen=True)
class OrderWithItems:
    """Order with its items.
    
    Uses dataclass instead of Pydantic to handle ORM models.
    """
    
    order: Order
    items: list[OrderItem]


class GetOrderQuery(Query[GetOrderInput, OrderWithItems | None]):
    """CQRS Query: Get order by ID.
    
    Read-only operation with direct ORM access for better performance.
    Does NOT go through Repository or UnitOfWork (CQRS pattern).
    
    Example:
        query = GetOrderQuery()
        result = await query.execute(GetOrderInput(order_id=order_id))
        if result:
            return OrderResponse.from_entity(result.order)
    """
    
    async def execute(self, input: GetOrderInput) -> OrderWithItems | None:
        """Execute the query.
        
        Args:
            input: GetOrderInput with order ID
            
        Returns:
            OrderWithItems if found, None otherwise
        """
        # Direct ORM access (CQRS read optimization)
        order = await Order.objects().where(Order.id == input.order_id).first()
        if order is None:
            return None
        
        items: list[OrderItem] = []
        if input.include_items:
            items = await OrderItem.objects().where(
                OrderItem.order == input.order_id
            ).order_by(OrderItem.id)
        
        return OrderWithItems(order=order, items=items)

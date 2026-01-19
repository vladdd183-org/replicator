"""ListUserOrdersQuery - List orders for a user.

CQRS Query: Read-only operation with direct ORM access.
Does NOT use Repository — optimized for performance.
"""

from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.OrderModule.Models.Order import Order


class ListUserOrdersInput(BaseModel):
    """Input for list user orders query.
    
    Uses frozen Pydantic model for immutability.
    """
    
    model_config = ConfigDict(frozen=True)
    
    user_id: UUID
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


@dataclass(frozen=True)
class OrderListResult:
    """Result of order list query.
    
    Uses dataclass instead of Pydantic to handle ORM models.
    """
    
    orders: list[Order]
    total: int
    limit: int
    offset: int


class ListUserOrdersQuery(Query[ListUserOrdersInput, OrderListResult]):
    """CQRS Query: List orders for a user.
    
    Read-only operation with direct ORM access for better performance.
    Does NOT go through Repository or UnitOfWork (CQRS pattern).
    
    Example:
        query = ListUserOrdersQuery()
        result = await query.execute(ListUserOrdersInput(user_id=user_id))
        return OrderListResponse(orders=result.orders, total=result.total)
    """
    
    async def execute(self, input: ListUserOrdersInput) -> OrderListResult:
        """Execute the query.
        
        Args:
            input: ListUserOrdersInput with user ID and pagination
            
        Returns:
            OrderListResult with orders and pagination info
        """
        # Direct ORM access (CQRS read optimization)
        query = Order.objects().where(Order.user_id == input.user_id)
        count_query = Order.count().where(Order.user_id == input.user_id)
        
        total = await count_query
        orders = await (
            query
            .limit(input.limit)
            .offset(input.offset)
            .order_by(Order.created_at, ascending=False)
        )
        
        return OrderListResult(
            orders=orders,
            total=total,
            limit=input.limit,
            offset=input.offset,
        )

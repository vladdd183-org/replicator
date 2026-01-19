"""ListUserOrdersQuery - List orders for a user."""

from dataclasses import dataclass
from uuid import UUID

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.OrderModule.Data.Repositories.OrderRepository import OrderRepository
from src.Containers.AppSection.OrderModule.Models.Order import Order


@dataclass
class ListUserOrdersInput:
    """Input for list user orders query."""
    
    user_id: UUID
    limit: int = 50
    offset: int = 0


@dataclass
class OrderListResult:
    """Result of order list query."""
    
    orders: list[Order]
    total: int
    limit: int
    offset: int


class ListUserOrdersQuery(Query[ListUserOrdersInput, OrderListResult]):
    """Query: List orders for a user.
    
    Retrieves paginated list of orders for a specific user.
    """
    
    def __init__(self, order_repository: OrderRepository) -> None:
        """Initialize query with dependencies.
        
        Args:
            order_repository: Repository for orders
        """
        self.order_repository = order_repository
    
    async def execute(self, input: ListUserOrdersInput) -> OrderListResult:
        """Execute the query.
        
        Args:
            input: ListUserOrdersInput with user ID and pagination
            
        Returns:
            OrderListResult with orders and pagination info
        """
        orders = await self.order_repository.find_by_user(
            user_id=input.user_id,
            limit=input.limit,
            offset=input.offset,
        )
        
        total = await self.order_repository.count_by_user(input.user_id)
        
        return OrderListResult(
            orders=orders,
            total=total,
            limit=input.limit,
            offset=input.offset,
        )

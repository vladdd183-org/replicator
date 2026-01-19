"""CreateOrderAction - Simple order creation without saga.

For simple cases where saga is not needed (single service, no external calls).
For distributed transactions, use StartCreateOrderWorkflowAction (Temporal) instead.
"""

from decimal import Decimal

from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.OrderModule.Data.Schemas.Requests import CreateOrderRequest
from src.Containers.AppSection.OrderModule.Data.UnitOfWork import OrderUnitOfWork
from src.Containers.AppSection.OrderModule.Models.Order import Order, OrderStatus
from src.Containers.AppSection.OrderModule.Models.OrderItem import OrderItem
from src.Containers.AppSection.OrderModule.Errors import OrderError, EmptyOrderError
from src.Containers.AppSection.OrderModule.Events import OrderCreated


class CreateOrderAction(Action[CreateOrderRequest, Order, OrderError]):
    """Use Case: Create a simple order.
    
    Creates order directly without saga orchestration.
    Use for simple cases without external service calls.
    
    Steps:
    1. Validate request
    2. Create order entity
    3. Create order items
    4. Calculate total
    5. Persist to database
    6. Publish OrderCreated event
    """
    
    def __init__(self, uow: OrderUnitOfWork) -> None:
        """Initialize action with dependencies.
        
        Args:
            uow: Unit of Work for data operations
        """
        self.uow = uow
    
    async def run(self, data: CreateOrderRequest) -> Result[Order, OrderError]:
        """Execute the create order use case.
        
        Args:
            data: CreateOrderRequest with order data
            
        Returns:
            Result[Order, OrderError]: Success with order or Failure
        """
        # Validate items
        if not data.items:
            return Failure(EmptyOrderError())
        
        # Calculate total
        total_amount = data.total_amount
        
        # Create order
        order = Order(
            user_id=data.user_id,
            status=OrderStatus.PENDING.value,
            total_amount=total_amount,
            currency=data.currency,
            shipping_address=data.shipping_address,
            notes=data.notes,
        )
        
        async with self.uow:
            # Save order
            await self.uow.orders.add(order)
            
            # Create order items
            for item_data in data.items:
                item = OrderItem(
                    order=order.id,
                    product_id=item_data.product_id,
                    product_name=item_data.product_name,
                    sku=item_data.sku,
                    quantity=item_data.quantity,
                    unit_price=item_data.unit_price,
                    subtotal=item_data.unit_price * Decimal(str(item_data.quantity)),
                )
                await self.uow.items.add(item)
            
            # Publish event
            self.uow.add_event(OrderCreated(
                order_id=order.id,
                user_id=order.user_id,
                total_amount=str(total_amount),
                currency=data.currency,
                item_count=len(data.items),
            ))
            
            await self.uow.commit()
        
        return Success(order)

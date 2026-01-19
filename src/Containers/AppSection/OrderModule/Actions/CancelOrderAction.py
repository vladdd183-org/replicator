"""CancelOrderAction - Cancel an existing order."""

from uuid import UUID

from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.OrderModule.Data.UnitOfWork import OrderUnitOfWork
from src.Containers.AppSection.OrderModule.Models.Order import Order, OrderStatus
from src.Containers.AppSection.OrderModule.Errors import (
    OrderError,
    OrderNotFoundError,
    OrderCancellationError,
)
from src.Containers.AppSection.OrderModule.Events import OrderCancelled


class CancelOrderInput:
    """Input for cancel order action."""
    
    def __init__(
        self,
        order_id: UUID,
        reason: str,
        request_refund: bool = True,
    ) -> None:
        self.order_id = order_id
        self.reason = reason
        self.request_refund = request_refund


class CancelOrderAction(Action[CancelOrderInput, Order, OrderError]):
    """Use Case: Cancel an order.
    
    Cancels an order if it's in a cancellable state.
    Triggers refund and inventory release if applicable.
    
    Steps:
    1. Find order
    2. Validate cancellation is allowed
    3. Update order status
    4. Publish OrderCancelled event (triggers compensation)
    """
    
    def __init__(self, uow: OrderUnitOfWork) -> None:
        """Initialize action with dependencies.
        
        Args:
            uow: Unit of Work for data operations
        """
        self.uow = uow
    
    async def run(self, data: CancelOrderInput) -> Result[Order, OrderError]:
        """Execute the cancel order use case.
        
        Args:
            data: CancelOrderInput with order ID and reason
            
        Returns:
            Result[Order, OrderError]: Success with cancelled order or Failure
        """
        # Find order
        order = await self.uow.orders.get(data.order_id)
        if order is None:
            return Failure(OrderNotFoundError(order_id=data.order_id))
        
        # Check if cancellation is allowed
        cancellable_statuses = {
            OrderStatus.PENDING.value,
            OrderStatus.INVENTORY_RESERVED.value,
            OrderStatus.PAYMENT_PROCESSING.value,
            OrderStatus.CONFIRMED.value,
        }
        
        if order.status not in cancellable_statuses:
            return Failure(OrderCancellationError(
                order_id=data.order_id,
                status=order.status,
            ))
        
        async with self.uow:
            # Update status
            order.status = OrderStatus.CANCELLED.value
            await self.uow.orders.update(order)
            
            # Publish event (triggers refund and inventory release)
            self.uow.add_event(OrderCancelled(
                order_id=order.id,
                user_id=order.user_id,
                reason=data.reason,
                refund_amount=str(order.total_amount) if data.request_refund else "0.00",
            ))
            
            await self.uow.commit()
        
        return Success(order)

"""CreateOrderSaga - Distributed transaction for order creation.

This saga orchestrates the complete order creation process:
1. Reserve inventory for all items
2. Process payment
3. Create order record
4. Send confirmation notification

If any step fails, previous steps are automatically compensated
(inventory released, payment refunded, etc.).
"""

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

import logfire
from pydantic import BaseModel
from returns.result import Result, Success, Failure

from src.Ship.Infrastructure.Saga import (
    Saga,
    SagaStep,
    SagaBuilder,
    SagaContext,
    NoOpCompensationStep,
    register_saga,
)
from src.Containers.AppSection.OrderModule.Models.Order import Order, OrderStatus
from src.Containers.AppSection.OrderModule.Data.UnitOfWork import OrderUnitOfWork
from src.Containers.AppSection.OrderModule.Data.Schemas.Requests import CreateOrderItemRequest
from src.Containers.AppSection.OrderModule.Tasks.ReserveInventoryTask import (
    ReserveInventoryTask,
    InventoryItem,
    ReserveInventoryInput,
    ReservationResult,
)
from src.Containers.AppSection.OrderModule.Tasks.ProcessPaymentTask import (
    ProcessPaymentTask,
    ProcessPaymentInput,
    PaymentResult,
)
from src.Containers.AppSection.OrderModule.Tasks.SendNotificationTask import (
    SendNotificationTask,
    OrderNotificationInput,
)
from src.Containers.AppSection.OrderModule.Errors import (
    OrderError,
    InventoryError,
    PaymentError,
)
from src.Containers.AppSection.OrderModule.Events import (
    OrderCreated,
)


# ============================================================================
# Saga Input/Output DTOs
# ============================================================================

class CreateOrderSagaInput(BaseModel):
    """Input for CreateOrderSaga.
    
    Contains all data needed to create an order.
    """
    
    user_id: UUID
    items: list[CreateOrderItemRequest]
    shipping_address: str
    currency: str = "USD"
    notes: str | None = None
    
    @property
    def total_amount(self) -> Decimal:
        """Calculate total order amount."""
        return sum(
            item.unit_price * Decimal(str(item.quantity))
            for item in self.items
        )


class CreateOrderSagaOutput(BaseModel):
    """Output from CreateOrderSaga.
    
    Contains the created order and related IDs.
    """
    
    order_id: UUID
    reservation_id: str
    payment_id: str
    total_amount: str


# ============================================================================
# Saga Step 1: Reserve Inventory
# ============================================================================

@dataclass
class ReserveInventoryStep(SagaStep[CreateOrderSagaInput, ReservationResult, InventoryError]):
    """Step 1: Reserve inventory for all order items.
    
    Calls inventory service to reserve stock for all items.
    On failure, no compensation needed (nothing was reserved yet).
    On compensation (later step failed), releases the reservation.
    """
    
    name: str = "reserve_inventory"
    description: str = "Reserve inventory for order items"
    reserve_inventory_task: ReserveInventoryTask = field(default_factory=ReserveInventoryTask)
    
    # Store order_id for compensation
    _current_order_id: UUID | None = field(default=None, repr=False)
    
    async def execute(
        self,
        input: CreateOrderSagaInput,
    ) -> Result[ReservationResult, InventoryError]:
        """Reserve inventory for all items."""
        from uuid import uuid4
        
        # Generate order_id for tracking (will be used by later steps)
        order_id = uuid4()
        self._current_order_id = order_id
        
        logfire.info(
            f"🔹 Step: Reserve inventory for {len(input.items)} items",
            order_id=str(order_id),
        )
        
        # Convert items to inventory format
        inventory_items = [
            InventoryItem(
                product_id=item.product_id,
                quantity=item.quantity,
                product_name=item.product_name,
            )
            for item in input.items
        ]
        
        reservation_input = ReserveInventoryInput(
            order_id=order_id,
            user_id=input.user_id,
            items=inventory_items,
        )
        
        result = await self.reserve_inventory_task.run(reservation_input)
        
        match result:
            case Success(reservation):
                logfire.info(
                    f"✅ Inventory reserved",
                    reservation_id=reservation.reservation_id,
                )
                return Success(reservation)
            case Failure(error):
                logfire.error(
                    f"❌ Inventory reservation failed",
                    error=str(error),
                )
                return Failure(error)
    
    async def compensate(
        self,
        input: CreateOrderSagaInput,
        output: ReservationResult,
    ) -> None:
        """Release inventory reservation."""
        logfire.info(
            f"🔙 Compensating: Releasing inventory reservation",
            reservation_id=output.reservation_id,
        )
        
        await self.reserve_inventory_task.cancel_reservation(output.reservation_id)


# ============================================================================
# Saga Step 2: Process Payment
# ============================================================================

@dataclass
class ProcessPaymentStep(SagaStep[ReservationResult, PaymentResult, PaymentError]):
    """Step 2: Process payment for the order.
    
    Receives inventory reservation from previous step.
    Charges customer's payment method.
    On compensation, issues refund.
    """
    
    name: str = "process_payment"
    description: str = "Process payment for order"
    process_payment_task: ProcessPaymentTask = field(default_factory=ProcessPaymentTask)
    
    # Need original order input for payment amount
    _saga_input: CreateOrderSagaInput | None = field(default=None, repr=False)
    
    async def on_execute_start(
        self,
        input: ReservationResult,
        context: SagaContext,
    ) -> None:
        """Store saga input from context for payment processing."""
        # In real implementation, would get this from context or DI
        pass
    
    async def execute(
        self,
        input: ReservationResult,
    ) -> Result[PaymentResult, PaymentError]:
        """Process payment."""
        logfire.info(
            f"🔹 Step: Processing payment",
            order_id=str(input.order_id),
            reservation_id=input.reservation_id,
        )
        
        # Calculate amount from reserved items
        # In production, amount would come from saga context or be passed properly
        total_amount = Decimal("99.99")  # Placeholder - would come from context
        
        payment_input = ProcessPaymentInput(
            order_id=input.order_id,
            user_id=input.order_id,  # Would be actual user_id from context
            amount=total_amount,
            currency="USD",
            reservation_id=input.reservation_id,
        )
        
        result = await self.process_payment_task.run(payment_input)
        
        match result:
            case Success(payment):
                logfire.info(
                    f"✅ Payment processed",
                    payment_id=payment.payment_id,
                    amount=payment.amount,
                )
                return Success(payment)
            case Failure(error):
                logfire.error(
                    f"❌ Payment failed",
                    error=str(error),
                )
                return Failure(error)
    
    async def compensate(
        self,
        input: ReservationResult,
        output: PaymentResult,
    ) -> None:
        """Refund payment."""
        logfire.info(
            f"🔙 Compensating: Refunding payment",
            payment_id=output.payment_id,
        )
        
        await self.process_payment_task.refund(
            payment_id=output.payment_id,
            reason="Order saga compensation",
        )


# ============================================================================
# Saga Step 3: Create Order Record
# ============================================================================

@dataclass
class CreateOrderRecordStep(SagaStep[PaymentResult, Order, OrderError]):
    """Step 3: Create order record in database.
    
    Receives payment confirmation from previous step.
    Creates order and order items in database.
    On compensation, marks order as cancelled/failed.
    """
    
    name: str = "create_order"
    description: str = "Create order record in database"
    uow: OrderUnitOfWork = field(default_factory=OrderUnitOfWork)
    
    # Need saga input for order details
    _saga_input: CreateOrderSagaInput | None = field(default=None, repr=False)
    _reservation: ReservationResult | None = field(default=None, repr=False)
    
    async def execute(
        self,
        input: PaymentResult,
    ) -> Result[Order, OrderError]:
        """Create order record."""
        logfire.info(
            f"🔹 Step: Creating order record",
            order_id=str(input.order_id),
            payment_id=input.payment_id,
        )
        
        try:
            # Create order entity
            order = Order(
                id=input.order_id,
                user_id=input.order_id,  # Would be actual user_id
                status=OrderStatus.CONFIRMED.value,
                total_amount=Decimal(input.amount),
                currency=input.currency,
                payment_id=input.payment_id,
                shipping_address="123 Main St",  # Would come from saga input
            )
            
            async with self.uow:
                await self.uow.orders.add(order)
                
                # Add event for listeners
                self.uow.add_event(OrderCreated(
                    order_id=order.id,
                    user_id=order.user_id,
                    total_amount=str(order.total_amount),
                    currency=order.currency,
                    item_count=1,  # Would be actual count
                ))
                
                await self.uow.commit()
            
            logfire.info(
                f"✅ Order created",
                order_id=str(order.id),
            )
            
            return Success(order)
            
        except Exception as e:
            logfire.exception(
                f"💥 Failed to create order",
                error=str(e),
            )
            return Failure(OrderError(message=f"Failed to create order: {str(e)}"))
    
    async def compensate(
        self,
        input: PaymentResult,
        output: Order,
    ) -> None:
        """Mark order as failed/cancelled."""
        logfire.info(
            f"🔙 Compensating: Marking order as failed",
            order_id=str(output.id),
        )
        
        try:
            async with self.uow:
                await self.uow.orders.update_status(
                    output.id,
                    OrderStatus.FAILED,
                )
                await self.uow.commit()
        except Exception as e:
            logfire.error(
                f"Failed to mark order as failed",
                order_id=str(output.id),
                error=str(e),
            )


# ============================================================================
# Saga Step 4: Send Notification (No Compensation)
# ============================================================================

@dataclass
class SendOrderConfirmationStep(NoOpCompensationStep[Order, bool, OrderError]):
    """Step 4: Send order confirmation notification.
    
    Sends confirmation email/notification to customer.
    This step has no compensation - notifications don't need rollback
    (user will get cancellation notice instead).
    """
    
    name: str = "send_confirmation"
    description: str = "Send order confirmation notification"
    send_notification_task: SendNotificationTask = field(default_factory=SendNotificationTask)
    retryable: bool = False  # Don't retry notifications
    
    async def execute(
        self,
        input: Order,
    ) -> Result[bool, OrderError]:
        """Send order confirmation."""
        logfire.info(
            f"🔹 Step: Sending order confirmation",
            order_id=str(input.id),
        )
        
        try:
            notification_input = OrderNotificationInput(
                user_id=input.user_id,
                order_id=input.id,
                notification_type="order_created",
                message=f"Your order has been confirmed! Order ID: {input.id}",
            )
            
            result = await self.send_notification_task.run(notification_input)
            
            logfire.info(
                f"✅ Confirmation sent",
                order_id=str(input.id),
            )
            
            return Success(result)
            
        except Exception as e:
            # Don't fail the saga for notification errors
            logfire.warning(
                f"⚠️ Notification failed (non-critical)",
                order_id=str(input.id),
                error=str(e),
            )
            return Success(True)  # Continue anyway


# ============================================================================
# Saga Definition
# ============================================================================

def create_create_order_saga(
    reserve_inventory_task: ReserveInventoryTask | None = None,
    process_payment_task: ProcessPaymentTask | None = None,
    order_uow: OrderUnitOfWork | None = None,
    send_notification_task: SendNotificationTask | None = None,
) -> Saga[CreateOrderSagaInput]:
    """Create the CreateOrderSaga with injected dependencies.
    
    Args:
        reserve_inventory_task: Task for inventory operations
        process_payment_task: Task for payment operations
        order_uow: Unit of work for order persistence
        send_notification_task: Task for notifications
        
    Returns:
        Configured Saga instance
    """
    return (
        SagaBuilder[CreateOrderSagaInput]("CreateOrder")
        .with_description("Creates an order with inventory reservation and payment processing")
        .with_version("1.0")
        .with_timeout(300)  # 5 minute timeout
        .add_step(ReserveInventoryStep(
            reserve_inventory_task=reserve_inventory_task or ReserveInventoryTask(),
        ))
        .add_step(ProcessPaymentStep(
            process_payment_task=process_payment_task or ProcessPaymentTask(),
        ))
        .add_step(CreateOrderRecordStep(
            uow=order_uow or OrderUnitOfWork(),
        ))
        .add_step(SendOrderConfirmationStep(
            send_notification_task=send_notification_task or SendNotificationTask(),
        ))
        .build()
    )


# Factory for TaskIQ worker registration
def create_order_saga_factory() -> Saga[CreateOrderSagaInput]:
    """Factory function for saga registry.
    
    Creates saga with default dependencies.
    In production, would use DI container.
    """
    return create_create_order_saga()


# Alias for convenience
CreateOrderSaga = create_create_order_saga


# Register saga for background execution
register_saga("CreateOrder", create_order_saga_factory)


__all__ = [
    "CreateOrderSaga",
    "create_create_order_saga",
    "create_order_saga_factory",
    "CreateOrderSagaInput",
    "CreateOrderSagaOutput",
    "ReserveInventoryStep",
    "ProcessPaymentStep",
    "CreateOrderRecordStep",
    "SendOrderConfirmationStep",
]

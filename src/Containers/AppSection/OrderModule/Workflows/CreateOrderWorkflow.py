"""CreateOrderWorkflow - Temporal Workflow for order creation saga.

This Workflow orchestrates the complete order creation process:
1. Create order record
2. Reserve inventory for all items
3. Process payment
4. Schedule delivery
5. Send confirmation notification

If any step fails, previous steps are automatically compensated
(order cancelled, inventory released, payment refunded, etc.).

Architecture:
- @workflow.defn makes this a Temporal Workflow
- Uses SagaCompensations for automatic rollback
- Returns Result[OrderWorkflowResult, OrderWorkflowError] for Railway integration
- Each step is a Temporal Activity with its own retry policy

Usage:
    # From Action:
    handle = await temporal_client.start_workflow(
        CreateOrderWorkflow.run,
        CreateOrderWorkflowInput(...),
        id=f"order-{uuid4()}",
        task_queue="orders",
    )
    
    # Check status:
    result = await handle.result()
"""

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field
from temporalio import workflow
from temporalio.common import RetryPolicy
from returns.result import Result, Success, Failure

from src.Ship.Core.Errors import BaseError
with workflow.unsafe.imports_passed_through():
    from src.Ship.Infrastructure.Temporal.Saga import SagaCompensations
    from src.Containers.AppSection.OrderModule.Activities import (
        # Main activities
        create_order,
        reserve_inventory,
        charge_payment,
        schedule_delivery,
        send_order_confirmation,
        # Compensation activities
        cancel_order,
        cancel_reservation,
        refund_payment,
        cancel_delivery,
        send_order_cancelled,
        # DTOs
        CreateOrderInput,
        CreateOrderOutput,
        ReserveInventoryInput,
        ReservationOutput,
        ChargePaymentInput,
        PaymentOutput,
        ScheduleDeliveryInput,
        DeliveryOutput,
        NotificationInput,
    )
    from src.Containers.AppSection.OrderModule.Activities.CreateOrderActivity import OrderItemInput


# =============================================================================
# Workflow Input/Output DTOs
# =============================================================================

class CreateOrderWorkflowInput(BaseModel):
    """Input for CreateOrderWorkflow.
    
    Contains all data needed to create an order via workflow.
    This is the top-level input passed to the workflow.
    
    Attributes:
        user_id: Customer placing the order
        items: List of order items
        shipping_address: Delivery address
        currency: Payment currency
        notes: Optional order notes
    """
    
    user_id: UUID
    items: list[OrderItemInput]
    shipping_address: str
    currency: str = "USD"
    notes: str | None = None
    
    # Options
    expedited_shipping: bool = False
    
    @property
    def total_amount(self) -> Decimal:
        """Calculate total order amount."""
        return sum(
            Decimal(item.unit_price) * Decimal(str(item.quantity))
            for item in self.items
        )


class OrderWorkflowResult(BaseModel):
    """Successful result from CreateOrderWorkflow.
    
    Contains all IDs and details from the completed saga.
    
    Attributes:
        order_id: Created order UUID
        reservation_id: Inventory reservation ID
        payment_id: Payment transaction ID
        delivery_id: Delivery tracking ID
        tracking_number: Carrier tracking number
        status: Final order status
        total_amount: Total charged amount
    """
    
    order_id: UUID
    reservation_id: str
    payment_id: str
    delivery_id: str
    tracking_number: str
    status: str
    total_amount: str  # Decimal as string


class OrderWorkflowError(BaseError):
    """Error result from CreateOrderWorkflow.
    
    Contains failure details for debugging and user feedback.
    
    Attributes:
        message: Human-readable error message
        code: Error code for programmatic handling
        failed_step: Name of the step that failed
        compensations_run: List of compensations that were executed
    """
    
    message: str
    code: str = "ORDER_WORKFLOW_FAILED"
    http_status: int = 500
    failed_step: str | None = None
    compensations_run: list[str] = Field(default_factory=list)


# =============================================================================
# Workflow Definition
# =============================================================================

@workflow.defn(name="CreateOrderWorkflow")
class CreateOrderWorkflow:
    """Temporal Workflow for creating orders with saga compensation.
    
    This workflow orchestrates a distributed transaction across:
    - Order service (database)
    - Inventory service
    - Payment service
    - Delivery service
    - Notification service
    
    Temporal guarantees:
    - At-least-once execution of activities
    - Automatic retries based on RetryPolicy
    - Durable execution state (survives crashes)
    - Compensation execution on failure
    
    Example:
        @workflow.defn
        class CreateOrderWorkflow:
            @workflow.run
            async def run(self, data: CreateOrderWorkflowInput) -> Result[...]:
                comp = SagaCompensations()
                try:
                    # Step 1: Create order
                    order = await workflow.execute_activity(create_order, ...)
                    comp.add(cancel_order, order.order_id)
                    
                    # More steps...
                    
                    return Success(OrderWorkflowResult(...))
                except Exception as ex:
                    await comp.run_all()
                    return Failure(OrderWorkflowError(...))
    """
    
    def __init__(self) -> None:
        """Initialize workflow state."""
        self._order_id: UUID | None = None
        self._status: str = "pending"
        self._failed_step: str | None = None
    
    @workflow.query
    def get_status(self) -> str:
        """Query current workflow status.
        
        Can be called while workflow is running.
        
        Returns:
            Current status string
        """
        return self._status
    
    @workflow.query
    def get_order_id(self) -> UUID | None:
        """Query created order ID.
        
        Returns:
            Order UUID if created, None otherwise
        """
        return self._order_id
    
    @workflow.run
    async def run(
        self,
        data: CreateOrderWorkflowInput,
    ) -> Result[OrderWorkflowResult, OrderWorkflowError]:
        """Execute order creation saga.
        
        This is the main workflow method that orchestrates all steps.
        Uses SagaCompensations for automatic rollback on failure.
        
        Args:
            data: Workflow input with order details
            
        Returns:
            Result[OrderWorkflowResult, OrderWorkflowError]:
                Success with order details, or
                Failure with error info
        """
        workflow.logger.info(
            f"🎭 Starting CreateOrderWorkflow for user {data.user_id} "
            f"with {len(data.items)} items"
        )
        
        # Compensation tracker
        comp = SagaCompensations()
        compensations_run: list[str] = []
        
        # Get workflow ID for correlation
        workflow_id = workflow.info().workflow_id
        
        # Retry policies
        default_retry = RetryPolicy(
            maximum_attempts=3,
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            backoff_coefficient=2.0,
        )
        
        payment_retry = RetryPolicy(
            maximum_attempts=5,
            initial_interval=timedelta(seconds=2),
            maximum_interval=timedelta(seconds=60),
            backoff_coefficient=2.0,
        )
        
        try:
            self._status = "creating_order"
            
            # =================================================================
            # Step 1: Create Order Record
            # =================================================================
            workflow.logger.info("📦 Step 1: Creating order record")
            
            order_input = CreateOrderInput(
                workflow_id=workflow_id,
                user_id=data.user_id,
                items=data.items,
                shipping_address=data.shipping_address,
                currency=data.currency,
                notes=data.notes,
            )
            
            order: CreateOrderOutput = await workflow.execute_activity(
                create_order,
                order_input,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=default_retry,
            )
            
            self._order_id = order.order_id
            comp.add(cancel_order, order.order_id)
            
            workflow.logger.info(f"✅ Order created: {order.order_id}")
            
            # =================================================================
            # Step 2: Reserve Inventory
            # =================================================================
            self._status = "reserving_inventory"
            workflow.logger.info("📦 Step 2: Reserving inventory")
            
            reservation_input = ReserveInventoryInput(
                order_id=order.order_id,
                user_id=data.user_id,
                items=[
                    {"product_id": item.product_id, "quantity": item.quantity, "product_name": item.product_name}
                    for item in data.items
                ],
            )
            
            reservation: ReservationOutput = await workflow.execute_activity(
                reserve_inventory,
                reservation_input,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=default_retry,
            )
            
            comp.add(cancel_reservation, reservation.reservation_id)
            
            workflow.logger.info(f"✅ Inventory reserved: {reservation.reservation_id}")
            
            # =================================================================
            # Step 3: Process Payment
            # =================================================================
            self._status = "processing_payment"
            workflow.logger.info("💳 Step 3: Processing payment")
            
            payment_input = ChargePaymentInput(
                order_id=order.order_id,
                user_id=data.user_id,
                amount=order.total_amount,
                currency=data.currency,
                reservation_id=reservation.reservation_id,
            )
            
            payment: PaymentOutput = await workflow.execute_activity(
                charge_payment,
                payment_input,
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=payment_retry,
            )
            
            comp.add(refund_payment, payment.payment_id)
            
            workflow.logger.info(f"✅ Payment processed: {payment.payment_id}")
            
            # =================================================================
            # Step 4: Schedule Delivery
            # =================================================================
            self._status = "scheduling_delivery"
            workflow.logger.info("🚚 Step 4: Scheduling delivery")
            
            delivery_input = ScheduleDeliveryInput(
                order_id=order.order_id,
                shipping_address=data.shipping_address,
                user_id=data.user_id,
                items_count=len(data.items),
                expedited=data.expedited_shipping,
            )
            
            delivery: DeliveryOutput = await workflow.execute_activity(
                schedule_delivery,
                delivery_input,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=default_retry,
            )
            
            # Optional compensation for delivery
            comp.add(cancel_delivery, delivery.delivery_id)
            
            workflow.logger.info(
                f"✅ Delivery scheduled: {delivery.delivery_id}, "
                f"tracking: {delivery.tracking_number}"
            )
            
            # =================================================================
            # Step 5: Send Confirmation (No Compensation)
            # =================================================================
            self._status = "sending_confirmation"
            workflow.logger.info("📧 Step 5: Sending confirmation")
            
            notification_input = NotificationInput(
                user_id=data.user_id,
                order_id=order.order_id,
                notification_type="order_created",
                message=f"Your order has been confirmed! Order ID: {order.order_id}",
                data={
                    "tracking_number": delivery.tracking_number,
                    "estimated_delivery": delivery.estimated_delivery.isoformat(),
                },
            )
            
            # Don't fail saga if notification fails
            try:
                await workflow.execute_activity(
                    send_order_confirmation,
                    notification_input,
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=2),
                )
                workflow.logger.info("✅ Confirmation sent")
            except Exception as notify_error:
                workflow.logger.warning(
                    f"⚠️ Notification failed (non-critical): {notify_error}"
                )
            
            # =================================================================
            # Success!
            # =================================================================
            self._status = "completed"
            
            workflow.logger.info(
                f"🎉 CreateOrderWorkflow completed successfully! "
                f"Order: {order.order_id}"
            )
            
            # Clear compensations since we succeeded
            comp.clear()
            
            return Success(OrderWorkflowResult(
                order_id=order.order_id,
                reservation_id=reservation.reservation_id,
                payment_id=payment.payment_id,
                delivery_id=delivery.delivery_id,
                tracking_number=delivery.tracking_number,
                status="confirmed",
                total_amount=order.total_amount,
            ))
            
        except Exception as ex:
            # =================================================================
            # Failure - Run Compensations
            # =================================================================
            self._status = "compensating"
            self._failed_step = self._get_current_step_name()
            
            workflow.logger.error(
                f"❌ Order creation failed at step '{self._failed_step}': {ex}"
            )
            
            # Run all compensations in reverse order
            if not comp.is_empty:
                workflow.logger.info(
                    f"🔙 Running {len(comp)} compensations..."
                )
                
                errors = await comp.run_all()
                
                # Track which compensations ran
                compensations_run = [
                    name for name, err in zip(
                        ["cancel_delivery", "refund_payment", "cancel_reservation", "cancel_order"],
                        errors[::-1],  # Reverse to match order
                    )
                    if err is None
                ]
            
            # Send cancellation notice
            if self._order_id:
                try:
                    await workflow.execute_activity(
                        send_order_cancelled,
                        NotificationInput(
                            user_id=data.user_id,
                            order_id=self._order_id,
                            notification_type="order_cancelled",
                            message=f"Your order could not be processed. Reason: {str(ex)[:100]}",
                        ),
                        start_to_close_timeout=timedelta(seconds=30),
                        retry_policy=RetryPolicy(maximum_attempts=1),
                    )
                except Exception:
                    pass  # Ignore notification errors
            
            self._status = "failed"
            
            return Failure(OrderWorkflowError(
                message=f"Order creation failed: {str(ex)}",
                code="ORDER_CREATION_FAILED",
                failed_step=self._failed_step,
                compensations_run=compensations_run,
            ))
    
    def _get_current_step_name(self) -> str:
        """Get human-readable name of current step."""
        step_names = {
            "creating_order": "create_order",
            "reserving_inventory": "reserve_inventory",
            "processing_payment": "charge_payment",
            "scheduling_delivery": "schedule_delivery",
            "sending_confirmation": "send_confirmation",
        }
        return step_names.get(self._status, self._status)


# All Workflows for Worker registration
ALL_WORKFLOWS = [
    CreateOrderWorkflow,
]


__all__ = [
    "CreateOrderWorkflow",
    "CreateOrderWorkflowInput",
    "OrderWorkflowResult",
    "OrderWorkflowError",
    "ALL_WORKFLOWS",
]

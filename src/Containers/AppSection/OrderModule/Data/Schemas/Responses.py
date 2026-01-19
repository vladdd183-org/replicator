"""Order module response DTOs.

All response DTOs inherit from EntitySchema for consistent serialization.
"""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.Ship.Core.BaseSchema import EntitySchema


class OrderItemResponse(EntitySchema):
    """Response DTO for order item.

    Attributes:
        id: Item UUID
        product_id: Product UUID
        product_name: Product name
        sku: Product SKU
        quantity: Quantity ordered
        unit_price: Price per unit
        subtotal: Line item total
    """

    id: UUID
    product_id: UUID
    product_name: str
    sku: str | None = None
    quantity: int
    unit_price: str  # Decimal as string for JSON
    subtotal: str


class OrderResponse(EntitySchema):
    """Response DTO for order.

    Attributes:
        id: Order UUID
        user_id: Customer UUID
        status: Current order status
        total_amount: Order total
        currency: Payment currency
        item_count: Number of items
        shipping_address: Delivery address
        reservation_id: Inventory reservation reference
        payment_id: Payment transaction reference
        notes: Order notes
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID
    user_id: UUID
    status: str
    total_amount: str  # Decimal as string
    currency: str = "USD"
    item_count: int = 0
    shipping_address: str | None = None
    reservation_id: str | None = None
    payment_id: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse] = Field(default_factory=list)

    @classmethod
    def from_entity(
        cls,
        order,
        items: list | None = None,
    ) -> "OrderResponse":
        """Create response from Order entity.

        Args:
            order: Order entity
            items: Optional list of OrderItem entities

        Returns:
            OrderResponse instance
        """
        item_responses = []
        if items:
            item_responses = [
                OrderItemResponse(
                    id=item.id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    sku=item.sku,
                    quantity=item.quantity,
                    unit_price=str(item.unit_price),
                    subtotal=str(item.subtotal),
                )
                for item in items
            ]

        return cls(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            total_amount=str(order.total_amount),
            currency=order.currency,
            item_count=len(item_responses),
            shipping_address=order.shipping_address,
            reservation_id=order.reservation_id,
            payment_id=order.payment_id,
            notes=order.notes,
            created_at=order.created_at,
            updated_at=order.updated_at,
            items=item_responses,
        )


class OrderListResponse(EntitySchema):
    """Response DTO for order list.

    Attributes:
        orders: List of orders
        total: Total count
        limit: Page size
        offset: Page offset
    """

    orders: list[OrderResponse]
    total: int
    limit: int
    offset: int


class OrderSagaResponse(EntitySchema):
    """Response DTO for legacy saga execution result.

    DEPRECATED: Use WorkflowResultResponse instead.

    Attributes:
        saga_id: Saga execution UUID
        status: Execution status (completed, failed, pending)
        order_id: Created order UUID (if successful)
        error: Error message (if failed)
        failed_step: Step that failed (if failed)
        duration_ms: Execution duration
    """

    saga_id: UUID
    status: str
    order_id: UUID | None = None
    error: str | None = None
    failed_step: str | None = None
    duration_ms: float | None = None
    steps_completed: list[str] = Field(default_factory=list)


# =============================================================================
# Temporal Workflow Response DTOs
# =============================================================================


class WorkflowStartedResponse(EntitySchema):
    """Response for async workflow start (202 Accepted).

    Returned immediately after workflow is started.
    Use workflow_id to track status.

    Attributes:
        workflow_id: Temporal workflow ID for tracking
        run_id: Temporal run ID
        order_id: Generated order UUID
        status: Always "started" for this response
        task_queue: Temporal task queue name
    """

    workflow_id: str
    run_id: str
    order_id: UUID
    status: str = "started"
    task_queue: str = "orders"


class WorkflowStatusResponse(EntitySchema):
    """Response for workflow status query.

    Contains current state of workflow execution.

    Attributes:
        workflow_id: Temporal workflow ID
        status: Execution status (running, completed, failed, etc.)
        current_step: Current step being executed
        order_id: Order UUID if created
        is_running: Whether workflow is still running
        run_id: Temporal run ID
        task_queue: Temporal task queue name
    """

    workflow_id: str
    status: str
    current_step: str | None = None
    order_id: UUID | None = None
    is_running: bool = True
    run_id: str | None = None
    task_queue: str | None = None


class WorkflowResultResponse(EntitySchema):
    """Response for completed workflow result.

    Contains full result after workflow completes.
    Returned by sync execution endpoint.

    Attributes:
        workflow_id: Temporal workflow ID
        order_id: Created order UUID
        reservation_id: Inventory reservation ID
        payment_id: Payment transaction ID
        delivery_id: Delivery tracking ID
        tracking_number: Carrier tracking number
        status: Final order status
        total_amount: Total charged amount
        error: Error message if failed
    """

    workflow_id: str
    order_id: UUID | None = None
    reservation_id: str | None = None
    payment_id: str | None = None
    delivery_id: str | None = None
    tracking_number: str | None = None
    status: str
    total_amount: str | None = None
    error: str | None = None


__all__ = [
    "OrderItemResponse",
    "OrderResponse",
    "OrderListResponse",
    # Legacy
    "OrderSagaResponse",
    # Temporal Workflow
    "WorkflowStartedResponse",
    "WorkflowStatusResponse",
    "WorkflowResultResponse",
]

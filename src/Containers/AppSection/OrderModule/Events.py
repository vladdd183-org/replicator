"""OrderModule domain events.

All domain events for the Order module in one place.
Events are immutable (frozen) Pydantic models published after UoW commit.
"""

from uuid import UUID

from pydantic import Field

from src.Ship.Parents.Event import DomainEvent


class OrderCreated(DomainEvent):
    """Event raised when a new order is created.

    Published after successful saga completion.

    Attributes:
        order_id: UUID of the created order
        user_id: UUID of the customer
        total_amount: Total order amount
        item_count: Number of items in the order
    """

    order_id: UUID
    user_id: UUID
    total_amount: str  # Decimal serialized as string
    currency: str = "USD"
    item_count: int


class OrderStatusChanged(DomainEvent):
    """Event raised when order status changes.

    Attributes:
        order_id: UUID of the order
        previous_status: Status before change
        new_status: Status after change
        reason: Optional reason for the change
    """

    order_id: UUID
    previous_status: str
    new_status: str
    reason: str | None = None


class OrderCancelled(DomainEvent):
    """Event raised when an order is cancelled.

    Triggers refund and inventory release processes.

    Attributes:
        order_id: UUID of the cancelled order
        user_id: UUID of the customer
        reason: Cancellation reason
        refund_amount: Amount to refund
    """

    order_id: UUID
    user_id: UUID
    reason: str
    refund_amount: str  # Decimal as string


class InventoryReserved(DomainEvent):
    """Event raised when inventory is reserved for an order.

    Attributes:
        order_id: UUID of the order
        reservation_id: Inventory system reservation ID
        items: List of reserved items with quantities
    """

    order_id: UUID
    reservation_id: str
    items: list[dict]  # [{product_id, quantity, ...}]


class InventoryReleased(DomainEvent):
    """Event raised when inventory reservation is released.

    Attributes:
        order_id: UUID of the order
        reservation_id: Inventory reservation ID that was released
        reason: Reason for release (e.g., order cancelled, payment failed)
    """

    order_id: UUID
    reservation_id: str
    reason: str


class PaymentProcessed(DomainEvent):
    """Event raised when payment is successfully processed.

    Attributes:
        order_id: UUID of the order
        payment_id: Payment gateway transaction ID
        amount: Amount charged
        payment_method: Payment method used
    """

    order_id: UUID
    payment_id: str
    amount: str  # Decimal as string
    currency: str = "USD"
    payment_method: str | None = None


class PaymentRefunded(DomainEvent):
    """Event raised when payment is refunded.

    Attributes:
        order_id: UUID of the order
        payment_id: Original payment transaction ID
        refund_id: Refund transaction ID
        amount: Amount refunded
        reason: Refund reason
    """

    order_id: UUID
    payment_id: str
    refund_id: str
    amount: str
    reason: str


class OrderShipped(DomainEvent):
    """Event raised when order is shipped.

    Attributes:
        order_id: UUID of the order
        tracking_number: Shipping tracking number
        carrier: Shipping carrier
        estimated_delivery: Estimated delivery date
    """

    order_id: UUID
    tracking_number: str
    carrier: str
    estimated_delivery: str | None = None


class OrderDelivered(DomainEvent):
    """Event raised when order is delivered.

    Attributes:
        order_id: UUID of the order
        delivered_at: Delivery timestamp
        signature: Delivery signature if required
    """

    order_id: UUID
    delivered_at: str  # ISO datetime string
    signature: str | None = None


# Saga-specific events


class OrderSagaStarted(DomainEvent):
    """Event raised when order creation saga starts.

    Attributes:
        saga_id: UUID of the saga execution
        order_data: Initial order request data
    """

    saga_id: UUID
    user_id: UUID
    item_count: int


class OrderSagaCompleted(DomainEvent):
    """Event raised when order creation saga completes successfully.

    Attributes:
        saga_id: UUID of the saga execution
        order_id: UUID of the created order
        duration_ms: Saga execution duration
    """

    saga_id: UUID
    order_id: UUID
    duration_ms: float


class OrderSagaFailed(DomainEvent):
    """Event raised when order creation saga fails.

    Attributes:
        saga_id: UUID of the saga execution
        failed_step: Name of the step that failed
        error: Error message
        compensations_run: List of compensations that were executed
    """

    saga_id: UUID
    failed_step: str
    error: str
    compensations_run: list[str] = Field(default_factory=list)


# Export all events
__all__ = [
    "InventoryReleased",
    "InventoryReserved",
    "OrderCancelled",
    "OrderCreated",
    "OrderDelivered",
    "OrderSagaCompleted",
    "OrderSagaFailed",
    "OrderSagaStarted",
    "OrderShipped",
    "OrderStatusChanged",
    "PaymentProcessed",
    "PaymentRefunded",
]

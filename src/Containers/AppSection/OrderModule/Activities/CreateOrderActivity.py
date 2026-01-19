"""CreateOrderActivity - Temporal Activity for order creation.

This Activity creates an order record in the database.
It's part of the CreateOrderWorkflow saga.

Architecture:
- @activity.defn decorator makes this a Temporal Activity
- Uses OrderUnitOfWork for database operations
- Returns CreateOrderOutput with order details

Compensation:
- cancel_order Activity marks order as cancelled
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from temporalio import activity

from src.Containers.AppSection.OrderModule.Data.Repositories.OrderItemRepository import (
    OrderItemRepository,
)
from src.Containers.AppSection.OrderModule.Data.Repositories.OrderRepository import OrderRepository
from src.Containers.AppSection.OrderModule.Data.UnitOfWork import OrderUnitOfWork
from src.Containers.AppSection.OrderModule.Models.Order import Order, OrderStatus
from src.Containers.AppSection.OrderModule.Models.OrderItem import OrderItem

# =============================================================================
# Input/Output DTOs
# =============================================================================


class OrderItemInput(BaseModel):
    """Item data for order creation."""

    product_id: UUID
    product_name: str
    sku: str | None = None
    quantity: int = Field(..., ge=1)
    unit_price: str  # Decimal as string for serialization


class CreateOrderInput(BaseModel):
    """Input for create_order activity.

    All data needed to create an order record.

    Attributes:
        workflow_id: Temporal workflow ID for correlation
        user_id: Customer placing the order
        items: List of order items
        shipping_address: Delivery address
        currency: Payment currency
        notes: Optional order notes
    """

    workflow_id: str
    user_id: UUID
    items: list[OrderItemInput]
    shipping_address: str
    currency: str = "USD"
    notes: str | None = None

    @property
    def total_amount(self) -> Decimal:
        """Calculate total order amount."""
        return sum(Decimal(item.unit_price) * Decimal(str(item.quantity)) for item in self.items)


class CreateOrderOutput(BaseModel):
    """Output from create_order activity.

    Contains created order details for next steps.

    Attributes:
        order_id: UUID of created order
        user_id: Customer UUID
        total_amount: Calculated total
        currency: Payment currency
        item_count: Number of items
        status: Order status
    """

    order_id: UUID
    user_id: UUID
    total_amount: str  # Decimal as string
    currency: str
    item_count: int
    status: str
    shipping_address: str
    created_at: datetime


# =============================================================================
# Create Order Activity
# =============================================================================


@activity.defn(name="create_order")
async def create_order(data: CreateOrderInput) -> CreateOrderOutput:
    """Create order record in database.

    This is a Temporal Activity that creates the order entity
    and all related order items.

    Args:
        data: Order creation input with items and details

    Returns:
        CreateOrderOutput with order ID and details

    Raises:
        Exception: On database errors (will trigger Temporal retry)
    """
    activity.logger.info(f"📦 Creating order for user {data.user_id} with {len(data.items)} items")

    # Calculate total
    total_amount = data.total_amount

    # Create order entity
    order = Order(
        id=uuid4(),
        user_id=data.user_id,
        status=OrderStatus.PENDING.value,
        total_amount=total_amount,
        currency=data.currency,
        shipping_address=data.shipping_address,
        notes=data.notes,
    )

    # Create UoW with repositories
    uow = OrderUnitOfWork(
        orders=OrderRepository(),
        items=OrderItemRepository(),
    )

    async with uow:
        # Save order
        await uow.orders.add(order)

        # Create order items
        for item_data in data.items:
            item = OrderItem(
                order=order.id,
                product_id=item_data.product_id,
                product_name=item_data.product_name,
                sku=item_data.sku,
                quantity=item_data.quantity,
                unit_price=Decimal(item_data.unit_price),
                subtotal=Decimal(item_data.unit_price) * Decimal(str(item_data.quantity)),
            )
            await uow.items.add(item)

        # Commit transaction
        await uow.commit()

    activity.logger.info(f"✅ Order created: {order.id}")

    return CreateOrderOutput(
        order_id=order.id,
        user_id=order.user_id,
        total_amount=str(total_amount),
        currency=order.currency,
        item_count=len(data.items),
        status=order.status,
        shipping_address=order.shipping_address,
        created_at=order.created_at,
    )


# =============================================================================
# Cancel Order Activity (Compensation)
# =============================================================================


class CancelOrderInput(BaseModel):
    """Input for cancel_order compensation."""

    model_config = {"frozen": True}

    order_id: UUID
    reason: str = "Workflow compensation"


@activity.defn(name="cancel_order")
async def cancel_order(order_id: UUID) -> bool:
    """Cancel/mark order as failed (compensation activity).

    Called during saga compensation to mark order as failed/cancelled.
    This is idempotent - already cancelled orders are ignored.

    Args:
        order_id: UUID of order to cancel

    Returns:
        True if cancelled, False if already cancelled
    """
    activity.logger.info(f"🔙 Cancelling order: {order_id}")

    uow = OrderUnitOfWork(
        orders=OrderRepository(),
        items=OrderItemRepository(),
    )

    async with uow:
        order = await uow.orders.get(order_id)

        if order is None:
            activity.logger.warning(f"⚠️ Order {order_id} not found for cancellation")
            return True  # Idempotent - treat as already cancelled

        if order.status in (OrderStatus.CANCELLED.value, OrderStatus.FAILED.value):
            activity.logger.info(f"ℹ️ Order {order_id} already cancelled/failed")
            return True

        # Update status
        await uow.orders.update_status(order_id, OrderStatus.FAILED)
        await uow.commit()

    activity.logger.info(f"✅ Order {order_id} marked as failed")
    return True


__all__ = [
    "CancelOrderInput",
    "CreateOrderInput",
    "CreateOrderOutput",
    "OrderItemInput",
    "cancel_order",
    "create_order",
]

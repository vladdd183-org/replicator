"""Order database model.

Represents a customer order with items, payment, and status tracking.
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from piccolo.columns import UUID, Decimal as DecimalColumn, Text, Timestamp, Varchar
from piccolo.columns.defaults.uuid import UUID4
from piccolo.columns.defaults.timestamp import TimestampNow
from piccolo.table import Table


class OrderStatus(str, Enum):
    """Order lifecycle status."""
    
    PENDING = "pending"
    """Order created, awaiting processing."""
    
    INVENTORY_RESERVED = "inventory_reserved"
    """Inventory has been reserved."""
    
    PAYMENT_PROCESSING = "payment_processing"
    """Payment is being processed."""
    
    PAYMENT_COMPLETED = "payment_completed"
    """Payment successful."""
    
    CONFIRMED = "confirmed"
    """Order confirmed and being prepared."""
    
    SHIPPED = "shipped"
    """Order has been shipped."""
    
    DELIVERED = "delivered"
    """Order delivered to customer."""
    
    CANCELLED = "cancelled"
    """Order was cancelled."""
    
    REFUNDED = "refunded"
    """Order was refunded."""
    
    FAILED = "failed"
    """Order processing failed."""


class Order(Table):
    """Order entity representing a customer purchase.
    
    Tracks the complete order lifecycle from creation to delivery,
    including payment and inventory information.
    
    Attributes:
        id: Unique order identifier (UUID)
        user_id: Customer who placed the order
        status: Current order status
        total_amount: Total order amount (calculated from items)
        currency: Payment currency (ISO 4217)
        reservation_id: Inventory reservation reference
        payment_id: Payment transaction reference
        shipping_address: Delivery address
        notes: Optional order notes
        created_at: Order creation timestamp
        updated_at: Last modification timestamp
    """
    
    # Primary key
    id = UUID(default=UUID4(), primary_key=True)
    
    # Customer reference
    user_id = UUID(null=False, index=True)
    
    # Order status
    status = Varchar(length=50, default=OrderStatus.PENDING.value, index=True)
    
    # Financial
    total_amount = DecimalColumn(
        digits=(12, 2),
        default=Decimal("0.00"),
        help_text="Total order amount",
    )
    currency = Varchar(length=3, default="USD")
    
    # External references
    reservation_id = Varchar(length=100, null=True, help_text="Inventory reservation ID")
    payment_id = Varchar(length=100, null=True, help_text="Payment transaction ID")
    
    # Delivery
    shipping_address = Text(null=True)
    
    # Metadata
    notes = Text(null=True)
    
    # Timestamps
    created_at = Timestamp(default=TimestampNow())
    updated_at = Timestamp(
        default=TimestampNow(),
        auto_update=datetime.now,
    )
    
    class Meta:
        tablename = "orders"
    
    def __str__(self) -> str:
        return f"Order({self.id}, status={self.status}, total={self.total_amount})"

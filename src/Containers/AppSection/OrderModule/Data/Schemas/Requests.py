"""Order module request DTOs.

All request DTOs are Pydantic models with validation.
All Request DTOs are frozen (immutable) for safety.
"""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateOrderItemRequest(BaseModel):
    """Request DTO for creating an order item.

    Attributes:
        product_id: UUID of the product
        product_name: Name of the product (snapshot)
        sku: Product SKU (optional)
        quantity: Number of units
        unit_price: Price per unit
    """

    model_config = ConfigDict(frozen=True)

    product_id: UUID
    product_name: str = Field(..., min_length=1, max_length=255)
    sku: str | None = Field(default=None, max_length=50)
    quantity: int = Field(..., ge=1, le=9999)
    unit_price: Decimal = Field(..., ge=Decimal("0.01"))

    @field_validator("unit_price", mode="before")
    @classmethod
    def validate_price(cls, v):
        """Ensure price has 2 decimal places."""
        if isinstance(v, str):
            v = Decimal(v)
        return v.quantize(Decimal("0.01"))


class CreateOrderRequest(BaseModel):
    """Request DTO for creating an order.

    Attributes:
        user_id: Customer placing the order
        items: List of order items
        shipping_address: Delivery address
        currency: Payment currency
        notes: Optional order notes
    """

    model_config = ConfigDict(frozen=True)

    user_id: UUID
    items: list[CreateOrderItemRequest] = Field(..., min_length=1)
    shipping_address: str = Field(..., min_length=10, max_length=1000)
    currency: str = Field(default="USD", max_length=3)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v):
        """Validate currency code."""
        valid_currencies = {"USD", "EUR", "GBP", "RUB", "CNY", "JPY"}
        if v.upper() not in valid_currencies:
            raise ValueError(f"Invalid currency: {v}. Supported: {valid_currencies}")
        return v.upper()

    @property
    def total_amount(self) -> Decimal:
        """Calculate total order amount."""
        return sum(item.unit_price * Decimal(str(item.quantity)) for item in self.items)

    @property
    def item_count(self) -> int:
        """Get total number of items."""
        return sum(item.quantity for item in self.items)


class UpdateOrderStatusRequest(BaseModel):
    """Request DTO for updating order status.

    Attributes:
        status: New status value
        reason: Optional reason for status change
    """

    model_config = ConfigDict(frozen=True)

    status: str = Field(..., max_length=50)
    reason: str | None = Field(default=None, max_length=500)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """Validate status is a known value."""
        valid_statuses = {
            "pending",
            "inventory_reserved",
            "payment_processing",
            "payment_completed",
            "confirmed",
            "shipped",
            "delivered",
            "cancelled",
            "refunded",
            "failed",
        }
        if v.lower() not in valid_statuses:
            raise ValueError(f"Invalid status: {v}. Valid: {valid_statuses}")
        return v.lower()


class CancelOrderRequest(BaseModel):
    """Request DTO for cancelling an order.

    Attributes:
        reason: Cancellation reason
        request_refund: Whether to process a refund
    """

    model_config = ConfigDict(frozen=True)

    reason: str = Field(..., min_length=5, max_length=500)
    request_refund: bool = Field(default=True)


__all__ = [
    "CancelOrderRequest",
    "CreateOrderItemRequest",
    "CreateOrderRequest",
    "UpdateOrderStatusRequest",
]

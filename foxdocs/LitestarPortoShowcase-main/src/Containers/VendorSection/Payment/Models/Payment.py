"""Payment model."""

from decimal import Decimal
from enum import Enum

from piccolo.columns import UUID, Decimal as DecimalColumn, ForeignKey, Text, Timestamptz, Varchar

from src.Ship.Parents import Model


class PaymentStatus(Enum):
    """Payment statuses."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(Model):
    """Payment model."""

    id = UUID(primary_key=True)
    user_id = ForeignKey("User", required=True)
    amount = DecimalColumn(digits=(10, 2), required=True)
    currency = Varchar(length=3, default="USD")
    status = Varchar(length=20, default=PaymentStatus.PENDING.value)
    payment_method_id = ForeignKey("PaymentMethod", required=True)
    description = Text(default="")
    external_id = Varchar(length=255, null=True)  # ID во внешней платежной системе
    created_at = Timestamptz()
    updated_at = Timestamptz()
    completed_at = Timestamptz(null=True)

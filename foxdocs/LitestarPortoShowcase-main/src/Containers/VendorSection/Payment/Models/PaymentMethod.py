"""Payment method model."""

from enum import Enum

from piccolo.columns import UUID, Boolean, ForeignKey, Text, Timestamptz, Varchar

from src.Ship.Parents import Model


class PaymentType(Enum):
    """Payment types."""
    
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    CRYPTO = "crypto"


class PaymentMethod(Model):
    """Payment method model."""

    id = UUID(primary_key=True)
    user_id = ForeignKey("User", required=True)
    type = Varchar(length=20, required=True)
    name = Varchar(length=100, required=True)  # e.g., "Visa ending in 1234"
    details = Text(default="{}")  # JSON with encrypted payment details
    is_default = Boolean(default=False)
    is_active = Boolean(default=True)
    created_at = Timestamptz()
    updated_at = Timestamptz()

"""PaymentModule request DTOs.

Request DTOs use Pydantic for validation.
All Request DTOs are frozen (immutable) for safety.
"""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreatePaymentRequest(BaseModel):
    """Request DTO for creating a payment.

    Attributes:
        user_id: User making the payment
        amount: Payment amount (positive)
        currency: Payment currency code
        description: Payment description
    """

    model_config = ConfigDict(frozen=True)

    user_id: UUID
    amount: Decimal = Field(..., gt=0, description="Payment amount (positive)")
    currency: str = Field(default="RUB", min_length=3, max_length=3, description="Currency code")
    description: str = Field(default="", max_length=500, description="Payment description")


class RefundPaymentRequest(BaseModel):
    """Request DTO for refunding a payment.

    Attributes:
        payment_id: Original payment ID to refund
        user_id: User receiving the refund
        amount: Refund amount (positive)
        currency: Currency code
        reason: Reason for refund
    """

    model_config = ConfigDict(frozen=True)

    payment_id: UUID
    user_id: UUID
    amount: Decimal = Field(..., gt=0, description="Refund amount (positive)")
    currency: str = Field(default="RUB", min_length=3, max_length=3, description="Currency code")
    reason: str = Field(default="", max_length=500, description="Reason for refund")

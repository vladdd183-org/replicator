"""PaymentModule response DTOs.

Response DTOs inherit from EntitySchema for automatic conversion.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from src.Ship.Core.BaseSchema import EntitySchema


class PaymentResponse(EntitySchema):
    """Response DTO for payment operation.
    
    Attributes:
        payment_id: Unique payment identifier
        user_id: User who made the payment
        amount: Payment amount
        currency: Payment currency
        status: Payment status (success, failed, pending)
        provider_transaction_id: Transaction ID from provider
        processed_at: When payment was processed
        message: Additional message
    """
    
    payment_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str
    status: str
    provider_transaction_id: str | None = None
    processed_at: datetime | None = None
    message: str = ""


class RefundResponse(EntitySchema):
    """Response DTO for refund operation.
    
    Attributes:
        refund_id: Unique refund identifier
        payment_id: Original payment ID
        user_id: User who received the refund
        amount: Refund amount
        currency: Currency
        status: Refund status
        processed_at: When refund was processed
        message: Additional message
    """
    
    refund_id: UUID
    payment_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str
    status: str
    processed_at: datetime | None = None
    message: str = ""




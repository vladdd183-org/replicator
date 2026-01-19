"""PaymentModule domain events.

Events for tracking payment operations.
"""

from decimal import Decimal
from uuid import UUID

from src.Ship.Parents.Event import DomainEvent


class PaymentCreated(DomainEvent):
    """Event raised when a payment is created.

    Attributes:
        payment_id: Unique payment identifier
        user_id: User who initiated the payment
        amount: Payment amount
        currency: Payment currency
        status: Payment status (defaults to pending)
    """

    payment_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str
    status: str = "pending"


class PaymentProcessed(DomainEvent):
    """Event raised when a payment is successfully processed.

    Attributes:
        payment_id: Unique payment identifier
        user_id: User who made the payment
        amount: Payment amount
        currency: Payment currency
        provider_transaction_id: Transaction ID from payment provider
    """

    payment_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str
    provider_transaction_id: str | None = None


class PaymentFailed(DomainEvent):
    """Event raised when a payment fails.

    Attributes:
        payment_id: Unique payment identifier
        user_id: User who attempted the payment
        amount: Payment amount
        currency: Payment currency
        error_message: Description of the failure
    """

    payment_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str
    error_message: str


class PaymentRefunded(DomainEvent):
    """Event raised when a payment is refunded.

    Attributes:
        payment_id: Original payment identifier
        refund_id: Refund transaction identifier
        user_id: User who received the refund
        amount: Refunded amount
        currency: Payment currency
    """

    payment_id: UUID
    refund_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str


__all__ = ["PaymentCreated", "PaymentFailed", "PaymentProcessed", "PaymentRefunded"]

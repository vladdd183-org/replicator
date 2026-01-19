"""Gateway DTOs and Errors for UserModule.

This module defines the data types (DTOs) and errors used by
UserModule's gateways for inter-module communication.

Important: These are UserModule's OWN types, not imported from
provider modules. This ensures loose coupling - UserModule doesn't
depend on internal types of PaymentModule.

DTO Design Principles:
1. Minimal - only fields UserModule actually needs
2. Immutable - frozen Pydantic models
3. Self-contained - no imports from provider modules
4. Serializable - JSON-compatible for HTTP transport

Error Design:
- Gateway-specific errors inherit from GatewayError
- Domain-specific errors (PaymentDeclined) are separate
- Allows both generic and specific error handling
"""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, ClassVar
from uuid import UUID

from pydantic import BaseModel, Field

from src.Ship.Core.Errors import ErrorWithTemplate
from src.Ship.Core.GatewayErrors import GatewayError

# ============================================================================
# ENUMS
# ============================================================================


class PaymentStatus(StrEnum):
    """Payment status enum.

    Represents the state of a payment from UserModule's perspective.
    Simplified compared to PaymentModule's internal statuses.
    """

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class Currency(StrEnum):
    """Supported currencies.

    ISO 4217 currency codes that UserModule works with.
    """

    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


# ============================================================================
# REQUEST DTOs
# ============================================================================


class PaymentRequest(BaseModel):
    """Request DTO for creating a payment.

    UserModule's view of payment creation request.
    Adapter maps this to PaymentModule's internal format.

    Attributes:
        user_id: User making the payment
        amount: Payment amount in minor units (kopecks/cents)
        currency: Payment currency code
        description: Optional payment description
        idempotency_key: Optional key for idempotent requests
        metadata: Optional additional data

    Example:
        request = PaymentRequest(
            user_id=user_id,
            amount=Decimal("1500.00"),
            currency="RUB",
            description="Premium subscription",
        )
    """

    model_config = {"frozen": True}

    user_id: UUID
    amount: Decimal = Field(..., gt=0, description="Payment amount (positive)")
    currency: str = Field(
        default="RUB",
        min_length=3,
        max_length=3,
        description="ISO 4217 currency code",
    )
    description: str = Field(default="", max_length=500)
    idempotency_key: str | None = Field(
        default=None,
        max_length=64,
        description="Idempotency key for safe retries",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class PaymentStatusRequest(BaseModel):
    """Request DTO for getting payment status.

    Attributes:
        payment_id: ID of the payment to check
    """

    model_config = {"frozen": True}

    payment_id: UUID


class RefundRequest(BaseModel):
    """Request DTO for refunding a payment.

    Attributes:
        payment_id: Original payment to refund
        amount: Refund amount (None = full refund)
        reason: Reason for refund
        idempotency_key: Optional key for idempotent requests
    """

    model_config = {"frozen": True}

    payment_id: UUID
    amount: Decimal | None = Field(
        default=None,
        gt=0,
        description="Refund amount (None = full refund)",
    )
    reason: str = Field(default="", max_length=500)
    idempotency_key: str | None = Field(
        default=None,
        max_length=64,
    )


# ============================================================================
# RESPONSE DTOs
# ============================================================================


class PaymentResult(BaseModel):
    """Result DTO for payment operations.

    UserModule's view of payment result.
    Adapter maps PaymentModule's internal result to this format.

    Attributes:
        payment_id: Unique payment identifier
        user_id: User who made the payment
        amount: Payment amount
        currency: Payment currency
        status: Current payment status
        created_at: When payment was created
        processed_at: When payment was processed (if completed)
        provider_reference: External payment provider reference
        message: Optional status message
    """

    model_config = {"frozen": True}

    payment_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str
    status: PaymentStatus
    created_at: datetime
    processed_at: datetime | None = None
    provider_reference: str | None = None
    message: str = ""


class RefundResult(BaseModel):
    """Result DTO for refund operations.

    Attributes:
        refund_id: Unique refund identifier
        payment_id: Original payment that was refunded
        amount: Refunded amount
        currency: Currency
        status: Refund status
        created_at: When refund was created
        processed_at: When refund was processed
        message: Optional status message
    """

    model_config = {"frozen": True}

    refund_id: UUID
    payment_id: UUID
    amount: Decimal
    currency: str
    status: PaymentStatus
    created_at: datetime
    processed_at: datetime | None = None
    message: str = ""


# ============================================================================
# ERRORS
# ============================================================================


class PaymentGatewayError(GatewayError):
    """Base error for PaymentGateway operations.

    All payment gateway errors inherit from this.
    service_name is always "payment" for these errors.
    """

    service_name: str = "payment"
    code: str = "PAYMENT_GATEWAY_ERROR"


class PaymentGatewayConnectionError(ErrorWithTemplate, PaymentGatewayError):
    """Error when cannot connect to payment service."""

    _message_template: ClassVar[str] = "Cannot connect to payment service: {details}"
    code: str = "PAYMENT_GATEWAY_CONNECTION"
    http_status: int = 503
    details: str = "Connection failed"


class PaymentGatewayTimeoutError(ErrorWithTemplate, PaymentGatewayError):
    """Error when payment request times out."""

    _message_template: ClassVar[str] = "Payment request timed out after {timeout_seconds}s"
    code: str = "PAYMENT_GATEWAY_TIMEOUT"
    http_status: int = 504
    timeout_seconds: float = 30.0


class PaymentDeclinedError(ErrorWithTemplate, PaymentGatewayError):
    """Error when payment is declined.

    This is a domain-specific error (not transport error).
    The payment request reached the service but was rejected.
    """

    _message_template: ClassVar[str] = "Payment declined: {reason}"
    code: str = "PAYMENT_DECLINED"
    http_status: int = 402  # Payment Required
    reason: str
    decline_code: str | None = None


class PaymentNotFoundError(ErrorWithTemplate, PaymentGatewayError):
    """Error when payment is not found."""

    _message_template: ClassVar[str] = "Payment with id {payment_id} not found"
    code: str = "PAYMENT_NOT_FOUND"
    http_status: int = 404
    payment_id: UUID


class RefundNotAllowedError(ErrorWithTemplate, PaymentGatewayError):
    """Error when refund is not allowed.

    Reasons:
    - Payment not in refundable state
    - Refund window expired
    - Amount exceeds original payment
    """

    _message_template: ClassVar[str] = "Refund not allowed for payment {payment_id}: {reason}"
    code: str = "REFUND_NOT_ALLOWED"
    http_status: int = 400
    payment_id: UUID
    reason: str


class InsufficientFundsError(ErrorWithTemplate, PaymentGatewayError):
    """Error when user has insufficient funds."""

    _message_template: ClassVar[str] = "Insufficient funds: required {amount} {currency}"
    code: str = "INSUFFICIENT_FUNDS"
    http_status: int = 402
    amount: Decimal
    currency: str


__all__ = [
    # Enums
    "PaymentStatus",
    "Currency",
    # Request DTOs
    "PaymentRequest",
    "PaymentStatusRequest",
    "RefundRequest",
    # Response DTOs
    "PaymentResult",
    "RefundResult",
    # Errors
    "PaymentGatewayError",
    "PaymentGatewayConnectionError",
    "PaymentGatewayTimeoutError",
    "PaymentDeclinedError",
    "PaymentNotFoundError",
    "RefundNotAllowedError",
    "InsufficientFundsError",
]

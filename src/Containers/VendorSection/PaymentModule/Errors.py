"""Payment module errors.

All errors are Pydantic frozen models with explicit http_status.
"""

from decimal import Decimal
from typing import ClassVar
from uuid import UUID

from src.Ship.Core.Errors import BaseError, ErrorWithTemplate


class PaymentError(BaseError):
    """Base error for PaymentModule."""
    
    code: str = "PAYMENT_ERROR"


class PaymentNotFoundError(ErrorWithTemplate, PaymentError):
    """Error raised when payment is not found."""
    
    _message_template: ClassVar[str] = "Payment with id {payment_id} not found"
    code: str = "PAYMENT_NOT_FOUND"
    http_status: int = 404
    payment_id: UUID


class PaymentProcessingError(ErrorWithTemplate, PaymentError):
    """Error raised when payment processing fails."""
    
    _message_template: ClassVar[str] = "Payment processing failed: {reason}"
    code: str = "PAYMENT_PROCESSING_FAILED"
    http_status: int = 500
    reason: str


class InsufficientFundsError(ErrorWithTemplate, PaymentError):
    """Error raised when there are insufficient funds."""
    
    _message_template: ClassVar[str] = "Insufficient funds: required {amount} {currency}"
    code: str = "INSUFFICIENT_FUNDS"
    http_status: int = 402  # Payment Required
    amount: Decimal
    currency: str


class PaymentAlreadyProcessedError(ErrorWithTemplate, PaymentError):
    """Error raised when trying to process already processed payment."""
    
    _message_template: ClassVar[str] = "Payment {payment_id} has already been processed"
    code: str = "PAYMENT_ALREADY_PROCESSED"
    http_status: int = 409
    payment_id: UUID


class RefundNotAllowedError(ErrorWithTemplate, PaymentError):
    """Error raised when refund is not allowed."""
    
    _message_template: ClassVar[str] = "Refund not allowed for payment {payment_id}: {reason}"
    code: str = "REFUND_NOT_ALLOWED"
    http_status: int = 400
    payment_id: UUID
    reason: str


class InvalidPaymentAmountError(ErrorWithTemplate, PaymentError):
    """Error raised when payment amount is invalid."""
    
    _message_template: ClassVar[str] = "Invalid payment amount: {amount}"
    code: str = "INVALID_PAYMENT_AMOUNT"
    http_status: int = 400
    amount: Decimal


__all__ = [
    "PaymentError",
    "PaymentNotFoundError",
    "PaymentProcessingError",
    "InsufficientFundsError",
    "PaymentAlreadyProcessedError",
    "RefundNotAllowedError",
    "InvalidPaymentAmountError",
]




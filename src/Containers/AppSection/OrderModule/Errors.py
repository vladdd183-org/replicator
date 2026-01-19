"""Order module errors.

All errors are Pydantic frozen models with explicit http_status.
Uses ErrorWithTemplate for automatic message generation.
"""

from decimal import Decimal
from typing import ClassVar
from uuid import UUID

from src.Ship.Core.Errors import BaseError, ErrorWithTemplate


class OrderError(BaseError):
    """Base error for OrderModule."""
    
    code: str = "ORDER_ERROR"


class OrderNotFoundError(ErrorWithTemplate, OrderError):
    """Error raised when order is not found."""
    
    _message_template: ClassVar[str] = "Order with id {order_id} not found"
    code: str = "ORDER_NOT_FOUND"
    http_status: int = 404
    order_id: UUID


class OrderItemNotFoundError(ErrorWithTemplate, OrderError):
    """Error raised when order item is not found."""
    
    _message_template: ClassVar[str] = "Order item with id {item_id} not found"
    code: str = "ORDER_ITEM_NOT_FOUND"
    http_status: int = 404
    item_id: UUID


class OrderAlreadyExistsError(ErrorWithTemplate, OrderError):
    """Error raised when duplicate order is detected."""
    
    _message_template: ClassVar[str] = "Order already exists for this transaction"
    code: str = "ORDER_ALREADY_EXISTS"
    http_status: int = 409


class InvalidOrderStatusError(ErrorWithTemplate, OrderError):
    """Error raised when order status transition is invalid."""
    
    _message_template: ClassVar[str] = "Cannot transition order {order_id} from '{current_status}' to '{target_status}'"
    code: str = "INVALID_ORDER_STATUS"
    http_status: int = 409
    order_id: UUID
    current_status: str
    target_status: str


class OrderCancellationError(ErrorWithTemplate, OrderError):
    """Error raised when order cannot be cancelled."""
    
    _message_template: ClassVar[str] = "Order {order_id} cannot be cancelled in '{status}' status"
    code: str = "ORDER_CANCELLATION_ERROR"
    http_status: int = 409
    order_id: UUID
    status: str


class EmptyOrderError(OrderError):
    """Error raised when trying to create order with no items."""
    
    code: str = "EMPTY_ORDER"
    http_status: int = 422
    message: str = "Order must contain at least one item"


class InvalidOrderAmountError(ErrorWithTemplate, OrderError):
    """Error raised when order amount is invalid."""
    
    _message_template: ClassVar[str] = "Invalid order amount: {amount}"
    code: str = "INVALID_ORDER_AMOUNT"
    http_status: int = 422
    amount: str


# External service errors for saga steps

class InventoryError(BaseError):
    """Base error for inventory operations."""
    
    code: str = "INVENTORY_ERROR"


class InsufficientInventoryError(ErrorWithTemplate, InventoryError):
    """Error raised when insufficient inventory available."""
    
    _message_template: ClassVar[str] = "Insufficient inventory for product {product_id}: requested {requested}, available {available}"
    code: str = "INSUFFICIENT_INVENTORY"
    http_status: int = 422
    product_id: UUID
    requested: int
    available: int


class InventoryReservationFailedError(ErrorWithTemplate, InventoryError):
    """Error raised when inventory reservation fails."""
    
    _message_template: ClassVar[str] = "Failed to reserve inventory: {reason}"
    code: str = "INVENTORY_RESERVATION_FAILED"
    http_status: int = 500
    reason: str


class InventoryServiceUnavailableError(InventoryError):
    """Error raised when inventory service is unavailable."""
    
    code: str = "INVENTORY_SERVICE_UNAVAILABLE"
    http_status: int = 503
    message: str = "Inventory service is temporarily unavailable"


class PaymentError(BaseError):
    """Base error for payment operations."""
    
    code: str = "PAYMENT_ERROR"


class PaymentDeclinedError(ErrorWithTemplate, PaymentError):
    """Error raised when payment is declined."""
    
    _message_template: ClassVar[str] = "Payment declined: {reason}"
    code: str = "PAYMENT_DECLINED"
    http_status: int = 402
    reason: str
    decline_code: str | None = None


class PaymentProcessingError(ErrorWithTemplate, PaymentError):
    """Error raised when payment processing fails."""
    
    _message_template: ClassVar[str] = "Payment processing failed: {reason}"
    code: str = "PAYMENT_PROCESSING_ERROR"
    http_status: int = 500
    reason: str


class PaymentGatewayUnavailableError(PaymentError):
    """Error raised when payment gateway is unavailable."""
    
    code: str = "PAYMENT_GATEWAY_UNAVAILABLE"
    http_status: int = 503
    message: str = "Payment gateway is temporarily unavailable"


class InsufficientFundsError(ErrorWithTemplate, PaymentError):
    """Error raised when customer has insufficient funds."""
    
    _message_template: ClassVar[str] = "Insufficient funds: required {required}, available {available}"
    code: str = "INSUFFICIENT_FUNDS"
    http_status: int = 402
    required: str
    available: str | None = None


# Temporal Workflow errors

class WorkflowError(OrderError):
    """Base error for Temporal Workflow operations."""
    
    code: str = "WORKFLOW_ERROR"


class WorkflowStartError(ErrorWithTemplate, WorkflowError):
    """Error raised when workflow cannot be started."""
    
    _message_template: ClassVar[str] = "Failed to start workflow for user {user_id}: {reason}"
    code: str = "WORKFLOW_START_FAILED"
    http_status: int = 500
    reason: str
    user_id: UUID


class WorkflowNotFoundError(ErrorWithTemplate, WorkflowError):
    """Error raised when workflow is not found."""
    
    _message_template: ClassVar[str] = "Workflow {workflow_id} not found"
    code: str = "WORKFLOW_NOT_FOUND"
    http_status: int = 404
    workflow_id: str


class WorkflowQueryError(ErrorWithTemplate, WorkflowError):
    """Error raised when workflow query fails."""
    
    _message_template: ClassVar[str] = "Failed to query workflow {workflow_id}: {reason}"
    code: str = "WORKFLOW_QUERY_FAILED"
    http_status: int = 500
    workflow_id: str
    reason: str


class WorkflowTimeoutError(ErrorWithTemplate, WorkflowError):
    """Error raised when workflow times out."""
    
    _message_template: ClassVar[str] = "Workflow {workflow_id} timed out after {timeout_seconds}s"
    code: str = "WORKFLOW_TIMEOUT"
    http_status: int = 504
    workflow_id: str
    timeout_seconds: int


class WorkflowCancelledError(ErrorWithTemplate, WorkflowError):
    """Error raised when workflow is cancelled."""
    
    _message_template: ClassVar[str] = "Workflow {workflow_id} was cancelled: {reason}"
    code: str = "WORKFLOW_CANCELLED"
    http_status: int = 409
    workflow_id: str
    reason: str = "User requested cancellation"


# Export all errors
__all__ = [
    # Order errors
    "OrderError",
    "OrderNotFoundError",
    "OrderItemNotFoundError",
    "OrderAlreadyExistsError",
    "InvalidOrderStatusError",
    "OrderCancellationError",
    "EmptyOrderError",
    "InvalidOrderAmountError",
    # Inventory errors
    "InventoryError",
    "InsufficientInventoryError",
    "InventoryReservationFailedError",
    "InventoryServiceUnavailableError",
    # Payment errors
    "PaymentError",
    "PaymentDeclinedError",
    "PaymentProcessingError",
    "PaymentGatewayUnavailableError",
    "InsufficientFundsError",
    # Workflow errors
    "WorkflowError",
    "WorkflowStartError",
    "WorkflowNotFoundError",
    "WorkflowQueryError",
    "WorkflowTimeoutError",
    "WorkflowCancelledError",
]

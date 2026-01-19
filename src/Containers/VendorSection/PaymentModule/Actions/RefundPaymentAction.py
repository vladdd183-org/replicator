"""RefundPaymentAction - Use case for refunding payments."""

from decimal import Decimal
from uuid import UUID, uuid4
from datetime import datetime, timezone

from pydantic import BaseModel
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.VendorSection.PaymentModule.Errors import (
    PaymentError,
    PaymentProcessingError,
    InvalidPaymentAmountError,
)


class RefundRequest(BaseModel):
    """Input for refund operation."""
    
    model_config = {"frozen": True}
    
    payment_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str = "RUB"
    reason: str = ""


class RefundResult(BaseModel):
    """Result of refund operation."""
    
    model_config = {"frozen": True}
    
    refund_id: UUID
    payment_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str
    status: str  # "success", "failed", "pending"
    processed_at: datetime | None = None
    message: str = ""


class RefundPaymentAction(Action[RefundRequest, RefundResult, PaymentError]):
    """Use Case: Refund a payment.
    
    This is a VIRTUAL implementation - simulates refund processing.
    
    Steps:
    1. Validate refund data
    2. Process refund (virtual)
    3. Return result
    
    Example:
        action = RefundPaymentAction()
        result = await action.run(RefundRequest(
            payment_id=payment_id,
            user_id=user_id,
            amount=Decimal("50.00"),
            reason="Customer request",
        ))
    """
    
    def __init__(self) -> None:
        """Initialize action."""
        pass
    
    async def run(self, data: RefundRequest) -> Result[RefundResult, PaymentError]:
        """Execute the refund payment use case.
        
        Args:
            data: RefundRequest with payment_id, user_id, amount
            
        Returns:
            Result[RefundResult, PaymentError]: Success with result or Failure with error
        """
        # Validate amount
        if data.amount <= Decimal("0"):
            return Failure(InvalidPaymentAmountError(amount=data.amount))
        
        try:
            refund_id = uuid4()
            processed_at = datetime.now(timezone.utc)
            
            # Virtual implementation - log refund
            try:
                import logfire
                logfire.info(
                    "💸 Refund processed (virtual)",
                    refund_id=str(refund_id),
                    payment_id=str(data.payment_id),
                    user_id=str(data.user_id),
                    amount=str(data.amount),
                    currency=data.currency,
                    reason=data.reason,
                )
            except ImportError:
                print(f"💸 Refund processed (virtual): {data.amount} {data.currency}")
            
            return Success(RefundResult(
                refund_id=refund_id,
                payment_id=data.payment_id,
                user_id=data.user_id,
                amount=data.amount,
                currency=data.currency,
                status="success",
                processed_at=processed_at,
                message="Refund processed successfully (virtual)",
            ))
            
        except Exception as e:
            return Failure(PaymentProcessingError(reason=str(e)))




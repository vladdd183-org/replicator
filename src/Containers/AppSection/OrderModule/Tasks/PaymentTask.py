"""Payment service integration task.

Provides payment processing and refund operations
for the order creation saga.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

import logfire
from pydantic import BaseModel
from returns.result import Result, Success, Failure

from src.Ship.Parents.Task import Task
from src.Containers.AppSection.OrderModule.Errors import (
    PaymentError,
    PaymentDeclinedError,
    PaymentProcessingError,
    InsufficientFundsError,
)


class ProcessPaymentInput(BaseModel):
    """Input for payment processing.
    
    Attributes:
        order_id: Order being paid for
        user_id: Customer making payment
        amount: Amount to charge
        currency: Payment currency
        reservation_id: Related inventory reservation
    """
    
    order_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str = "USD"
    reservation_id: str | None = None
    
    # Payment method details (simplified)
    payment_method: str = "card"
    card_last_four: str | None = None


class PaymentResult(BaseModel):
    """Result of payment processing.
    
    Attributes:
        payment_id: Transaction identifier
        order_id: Order that was paid
        amount: Amount charged
        status: Payment status
    """
    
    payment_id: str
    order_id: UUID
    amount: str  # Decimal as string
    currency: str
    status: str  # "completed", "pending", "failed"
    gateway_reference: str | None = None


class RefundResult(BaseModel):
    """Result of refund processing."""
    
    refund_id: str
    payment_id: str
    amount: str
    status: str


@dataclass
class PaymentTask(Task[ProcessPaymentInput, Result[PaymentResult, PaymentError]]):
    """Task for payment operations.
    
    Integrates with payment gateway to process payments and refunds.
    In production, this would call an external payment service (Stripe, etc.).
    
    For demonstration, this simulates payment processing.
    """
    
    # Configuration
    decline_threshold: Decimal = field(default=Decimal("10000.00"))  # Decline orders over this
    
    # Simulated payment store
    _payments: dict[str, PaymentResult] = field(default_factory=dict)
    _refunds: dict[str, RefundResult] = field(default_factory=dict)
    
    async def run(
        self,
        data: ProcessPaymentInput,
    ) -> Result[PaymentResult, PaymentError]:
        """Process a payment.
        
        Args:
            data: Payment request details
            
        Returns:
            Result with payment details or error
        """
        logfire.info(
            "💳 Processing payment",
            order_id=str(data.order_id),
            amount=str(data.amount),
            currency=data.currency,
        )
        
        try:
            # Simulate payment validation
            if data.amount > self.decline_threshold:
                logfire.warning(
                    "❌ Payment declined - amount too high",
                    amount=str(data.amount),
                    threshold=str(self.decline_threshold),
                )
                return Failure(PaymentDeclinedError(
                    reason=f"Amount exceeds limit of {self.decline_threshold}",
                    decline_code="AMOUNT_LIMIT_EXCEEDED",
                ))
            
            # Simulate random decline for testing (every 10th payment)
            # In production, this would be actual payment gateway logic
            
            # Create payment record
            payment_id = f"PAY-{uuid4().hex[:12].upper()}"
            gateway_ref = f"GW-{uuid4().hex[:8].upper()}"
            
            result = PaymentResult(
                payment_id=payment_id,
                order_id=data.order_id,
                amount=str(data.amount),
                currency=data.currency,
                status="completed",
                gateway_reference=gateway_ref,
            )
            
            # Store payment (in production, this would be API call)
            self._payments[payment_id] = result
            
            logfire.info(
                "✅ Payment processed",
                payment_id=payment_id,
                order_id=str(data.order_id),
                amount=str(data.amount),
            )
            
            return Success(result)
            
        except Exception as e:
            logfire.exception(
                "💥 Payment processing failed",
                order_id=str(data.order_id),
                error=str(e),
            )
            return Failure(PaymentProcessingError(reason=str(e)))
    
    async def refund(
        self,
        payment_id: str,
        amount: Decimal | None = None,
        reason: str = "Order cancelled",
    ) -> Result[RefundResult, PaymentError]:
        """Process a refund.
        
        Called during saga compensation to refund a payment.
        
        Args:
            payment_id: Payment to refund
            amount: Amount to refund (None = full refund)
            reason: Refund reason
            
        Returns:
            Result with refund details or error
        """
        logfire.info(
            "💸 Processing refund",
            payment_id=payment_id,
            amount=str(amount) if amount else "full",
            reason=reason,
        )
        
        try:
            payment = self._payments.get(payment_id)
            
            if not payment:
                logfire.warning(
                    "⚠️ Payment not found for refund",
                    payment_id=payment_id,
                )
                # Idempotent - treat as already refunded
                return Success(RefundResult(
                    refund_id=f"REF-{uuid4().hex[:8].upper()}",
                    payment_id=payment_id,
                    amount=str(amount or Decimal("0.00")),
                    status="already_refunded",
                ))
            
            refund_amount = amount or Decimal(payment.amount)
            refund_id = f"REF-{uuid4().hex[:12].upper()}"
            
            result = RefundResult(
                refund_id=refund_id,
                payment_id=payment_id,
                amount=str(refund_amount),
                status="completed",
            )
            
            self._refunds[refund_id] = result
            
            # Update payment status
            payment.status = "refunded"
            
            logfire.info(
                "✅ Refund processed",
                refund_id=refund_id,
                payment_id=payment_id,
                amount=str(refund_amount),
            )
            
            return Success(result)
            
        except Exception as e:
            logfire.exception(
                "💥 Refund processing failed",
                payment_id=payment_id,
                error=str(e),
            )
            return Failure(PaymentProcessingError(reason=f"Refund failed: {str(e)}"))
    
    async def get_payment(self, payment_id: str) -> PaymentResult | None:
        """Get payment details.
        
        Args:
            payment_id: Payment to look up
            
        Returns:
            Payment details if found
        """
        return self._payments.get(payment_id)


# Factory function for DI
def create_payment_task() -> PaymentTask:
    """Create PaymentTask instance."""
    return PaymentTask()


__all__ = [
    "PaymentTask",
    "ProcessPaymentInput",
    "PaymentResult",
    "RefundResult",
    "create_payment_task",
]

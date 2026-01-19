"""Task for processing payments.

This is an async Task because it involves I/O operations.
Virtual implementation for development - simulates payment processing.
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel

from src.Ship.Parents.Task import Task


class PaymentData(BaseModel):
    """Data for payment processing."""

    model_config = {"frozen": True}

    user_id: UUID
    amount: Decimal
    currency: str = "RUB"
    description: str = ""
    metadata: dict = {}


class PaymentResult(BaseModel):
    """Result of payment processing operation."""

    model_config = {"frozen": True}

    payment_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str
    status: str  # "success", "failed", "pending"
    provider_transaction_id: str | None = None
    processed_at: datetime | None = None
    message: str = ""


class ProcessPaymentTask(Task[PaymentData, PaymentResult]):
    """Async task for processing payments.

    Uses Task (async) because payment processing involves I/O.

    This is a VIRTUAL implementation - it simulates payment processing
    without real payment provider integration.

    In production, inject a real payment client:
    - Stripe
    - PayPal
    - YooKassa
    - Tinkoff

    Example:
        task = ProcessPaymentTask()
        result = await task.run(PaymentData(
            user_id=user_id,
            amount=Decimal("100.00"),
            currency="RUB",
            description="Order #123",
        ))
    """

    def __init__(self) -> None:
        """Initialize task."""
        # TODO: Inject real payment client when available
        pass

    async def run(self, data: PaymentData) -> PaymentResult:
        """Process payment (virtual implementation).

        Virtual logic:
        - Amounts < 1 fail (minimum amount)
        - Amounts ending with .99 simulate "pending" status
        - All other amounts succeed

        Args:
            data: PaymentData with user_id, amount, currency

        Returns:
            PaymentResult with status and payment_id
        """
        payment_id = uuid4()
        processed_at = datetime.now(UTC)

        # Virtual implementation - simulate payment provider
        try:
            import logfire

            logfire.info(
                "💳 Payment processing (virtual)",
                payment_id=str(payment_id),
                user_id=str(data.user_id),
                amount=str(data.amount),
                currency=data.currency,
            )
        except ImportError:
            print(f"💳 Payment processing (virtual): {data.amount} {data.currency}")

        # Simulate different scenarios based on amount
        if data.amount < Decimal("1.00"):
            return PaymentResult(
                payment_id=payment_id,
                user_id=data.user_id,
                amount=data.amount,
                currency=data.currency,
                status="failed",
                message="Minimum payment amount is 1.00",
            )

        # Simulate pending status for amounts ending with .99
        if str(data.amount).endswith(".99"):
            return PaymentResult(
                payment_id=payment_id,
                user_id=data.user_id,
                amount=data.amount,
                currency=data.currency,
                status="pending",
                provider_transaction_id=f"virt_pending_{uuid4().hex[:8]}",
                message="Payment is pending confirmation",
            )

        # Success case
        return PaymentResult(
            payment_id=payment_id,
            user_id=data.user_id,
            amount=data.amount,
            currency=data.currency,
            status="success",
            provider_transaction_id=f"virt_txn_{uuid4().hex[:12]}",
            processed_at=processed_at,
            message="Payment processed successfully (virtual)",
        )

"""PaymentGateway Protocol - interface for payment operations.

This is the "Port" in Ports & Adapters pattern.
UserModule (consumer) defines this interface, PaymentModule
implements it through adapters.

Design Decisions:
1. Protocol, not ABC - allows structural subtyping (duck typing)
2. runtime_checkable - enables isinstance() checks
3. Result[T, E] return types - consistent with Hyper-Porto
4. Async methods - all external calls should be async

Why UserModule Owns This Interface:
- Dependency Inversion Principle: high-level modules define interfaces
- UserModule knows what it needs, not how PaymentModule works
- Changes to PaymentModule internals don't affect this interface
- Easy to mock for testing UserModule

Methods:
- create_payment: Create and process a new payment
- get_payment_status: Check payment status by ID
- refund_payment: Refund full or partial payment

Usage:
    class SomeUserAction(Action[...]):
        payment_gateway: PaymentGateway  # Injected by Dishka

        async def run(self, data: ...) -> Result[...]:
            payment_result = await self.payment_gateway.create_payment(
                PaymentRequest(user_id=data.user_id, amount=data.amount)
            )

            match payment_result:
                case Success(payment):
                    # Payment successful
                    ...
                case Failure(PaymentDeclinedError() as e):
                    # Payment declined - domain error
                    ...
                case Failure(PaymentGatewayConnectionError() as e):
                    # Cannot reach payment service - infrastructure error
                    ...
"""

from typing import Protocol, runtime_checkable
from uuid import UUID

from returns.result import Result

from src.Containers.AppSection.UserModule.Gateways.Types import (
    PaymentGatewayError,
    PaymentRequest,
    PaymentResult,
    RefundRequest,
    RefundResult,
)


@runtime_checkable
class PaymentGateway(Protocol):
    """Gateway protocol for payment operations.

    Defines the interface that UserModule expects for payment functionality.
    Implemented by adapters:
    - DirectPaymentAdapter: Direct calls in monolith
    - HttpPaymentAdapter: HTTP calls in microservices

    All methods return Result[T, PaymentGatewayError] for explicit
    error handling without exceptions.

    Thread Safety:
        Implementations should be thread-safe for concurrent use.
        Multiple requests can call the same gateway instance.

    Idempotency:
        create_payment and refund_payment support idempotency_key.
        Same key = same result (for safe retries).
    """

    async def create_payment(
        self,
        request: PaymentRequest,
    ) -> Result[PaymentResult, PaymentGatewayError]:
        """Create and process a new payment.

        This is the primary method for initiating payments.
        The payment is processed synchronously - method returns
        when payment reaches terminal state (success/failed).

        Args:
            request: PaymentRequest with user_id, amount, currency

        Returns:
            Result containing:
            - Success(PaymentResult) - Payment processed successfully
            - Failure(PaymentDeclinedError) - Payment was declined
            - Failure(InsufficientFundsError) - Not enough funds
            - Failure(PaymentGatewayConnectionError) - Cannot reach service
            - Failure(PaymentGatewayTimeoutError) - Request timed out

        Idempotency:
            If request.idempotency_key is set, repeated calls with
            same key return same result without creating duplicate payments.

        Example:
            result = await gateway.create_payment(PaymentRequest(
                user_id=user_id,
                amount=Decimal("1000.00"),
                currency="RUB",
                description="Subscription payment",
                idempotency_key=f"sub_{user_id}_{period}",
            ))
        """
        ...

    async def get_payment_status(
        self,
        payment_id: UUID,
    ) -> Result[PaymentResult, PaymentGatewayError]:
        """Get current status of a payment.

        Used to check payment status, especially for async payments
        or after receiving webhooks.

        Args:
            payment_id: UUID of the payment to check

        Returns:
            Result containing:
            - Success(PaymentResult) - Payment found with current status
            - Failure(PaymentNotFoundError) - Payment doesn't exist
            - Failure(PaymentGatewayConnectionError) - Cannot reach service
            - Failure(PaymentGatewayTimeoutError) - Request timed out

        Example:
            result = await gateway.get_payment_status(payment_id)
            match result:
                case Success(payment) if payment.status == PaymentStatus.SUCCESS:
                    # Payment completed
                    ...
                case Success(payment) if payment.status == PaymentStatus.PENDING:
                    # Payment still processing
                    ...
        """
        ...

    async def refund_payment(
        self,
        request: RefundRequest,
    ) -> Result[RefundResult, PaymentGatewayError]:
        """Refund a payment (full or partial).

        Creates a refund for an existing payment. Supports both
        full refunds (amount=None) and partial refunds.

        Args:
            request: RefundRequest with payment_id, optional amount, reason

        Returns:
            Result containing:
            - Success(RefundResult) - Refund processed successfully
            - Failure(PaymentNotFoundError) - Payment doesn't exist
            - Failure(RefundNotAllowedError) - Refund not allowed
            - Failure(PaymentGatewayConnectionError) - Cannot reach service
            - Failure(PaymentGatewayTimeoutError) - Request timed out

        Constraints:
            - Cannot refund more than original amount
            - Cannot refund already fully refunded payment
            - Cannot refund failed payments

        Example:
            # Full refund
            result = await gateway.refund_payment(RefundRequest(
                payment_id=payment_id,
                reason="Customer request",
            ))

            # Partial refund
            result = await gateway.refund_payment(RefundRequest(
                payment_id=payment_id,
                amount=Decimal("500.00"),
                reason="Partial service cancellation",
            ))
        """
        ...

    async def verify_payment(
        self,
        payment_id: UUID,
        expected_amount: int | None = None,
        expected_currency: str | None = None,
    ) -> Result[bool, PaymentGatewayError]:
        """Verify payment is valid and matches expected parameters.

        Utility method to verify a payment exists and has expected
        amount/currency. Useful for webhook validation.

        Args:
            payment_id: Payment to verify
            expected_amount: Expected amount (None = don't check)
            expected_currency: Expected currency (None = don't check)

        Returns:
            Result containing:
            - Success(True) - Payment valid and matches
            - Success(False) - Payment exists but doesn't match
            - Failure(PaymentNotFoundError) - Payment doesn't exist
            - Failure(PaymentGatewayError) - Infrastructure error

        Example:
            # Verify webhook payload
            is_valid = await gateway.verify_payment(
                payment_id=webhook.payment_id,
                expected_amount=webhook.amount,
                expected_currency=webhook.currency,
            )
        """
        ...


__all__ = ["PaymentGateway"]

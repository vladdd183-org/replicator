"""ChargePaymentActivity - Temporal Activity for payment processing.

This Activity processes payment for an order.
In production, this would call a payment gateway (Stripe, etc.).

Architecture:
- @activity.defn decorator makes this a Temporal Activity
- Simulates payment processing (replace with actual gateway call)
- Returns PaymentOutput with transaction details

Compensation:
- refund_payment Activity issues a full refund
"""

from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel
from temporalio import activity

# =============================================================================
# Input/Output DTOs
# =============================================================================


class ChargePaymentInput(BaseModel):
    """Input for charge_payment activity.

    Attributes:
        order_id: Order UUID being paid
        user_id: Customer UUID
        amount: Amount to charge (as string for serialization)
        currency: Payment currency
        reservation_id: Related inventory reservation
    """

    order_id: UUID
    user_id: UUID
    amount: str  # Decimal as string
    currency: str = "USD"
    reservation_id: str | None = None

    # Payment method (simplified)
    payment_method: str = "card"


class PaymentOutput(BaseModel):
    """Output from charge_payment activity.

    Attributes:
        payment_id: Payment gateway transaction ID
        order_id: Associated order UUID
        amount: Amount charged
        currency: Payment currency
        status: Payment status
        gateway_reference: External gateway reference
    """

    payment_id: str
    order_id: UUID
    amount: str  # Decimal as string
    currency: str
    status: str  # "completed", "pending", "failed"
    gateway_reference: str | None = None


class RefundOutput(BaseModel):
    """Output from refund_payment activity."""

    refund_id: str
    payment_id: str
    amount: str
    status: str


# =============================================================================
# Charge Payment Activity
# =============================================================================


@activity.defn(name="charge_payment")
async def charge_payment(data: ChargePaymentInput) -> PaymentOutput:
    """Process payment for order.

    This is a Temporal Activity that charges the customer.
    In production, this would call Stripe, PayPal, etc.

    Temporal handles retries automatically based on RetryPolicy.

    Args:
        data: Payment request with amount and details

    Returns:
        PaymentOutput with transaction details

    Raises:
        Exception: On payment declined or gateway errors
    """
    activity.logger.info(
        f"💳 Processing payment for order {data.order_id}: {data.amount} {data.currency}"
    )

    # Validate amount
    amount = Decimal(data.amount)
    if amount <= 0:
        raise ValueError("Payment amount must be positive")

    # Check for decline threshold (simulation)
    if amount > Decimal("10000.00"):
        activity.logger.warning(f"❌ Payment declined - amount {amount} exceeds limit")
        raise Exception("Payment declined: Amount exceeds limit")

    # In production:
    # payment_intent = await stripe.PaymentIntent.create(
    #     amount=int(amount * 100),
    #     currency=data.currency.lower(),
    #     metadata={"order_id": str(data.order_id)},
    # )

    # Generate payment record
    payment_id = f"PAY-{uuid4().hex[:12].upper()}"
    gateway_ref = f"GW-{uuid4().hex[:8].upper()}"

    activity.logger.info(f"✅ Payment processed: {payment_id}")

    return PaymentOutput(
        payment_id=payment_id,
        order_id=data.order_id,
        amount=data.amount,
        currency=data.currency,
        status="completed",
        gateway_reference=gateway_ref,
    )


# =============================================================================
# Refund Payment Activity (Compensation)
# =============================================================================


class RefundInput(BaseModel):
    """Input for refund_payment compensation."""

    payment_id: str
    amount: str | None = None  # None = full refund
    reason: str = "Order cancelled"


@activity.defn(name="refund_payment")
async def refund_payment(payment_id: str) -> RefundOutput:
    """Issue refund for payment (compensation activity).

    Called during saga compensation to refund the customer.
    This is idempotent - already refunded payments are ignored.

    Args:
        payment_id: Payment ID to refund

    Returns:
        RefundOutput with refund details
    """
    activity.logger.info(f"💸 Processing refund for payment: {payment_id}")

    # In production:
    # try:
    #     refund = await stripe.Refund.create(
    #         payment_intent=payment_id,
    #     )
    # except stripe.error.InvalidRequestError:
    #     # Already refunded
    #     pass

    # Generate refund record
    refund_id = f"REF-{uuid4().hex[:12].upper()}"

    activity.logger.info(f"✅ Refund processed: {refund_id}")

    return RefundOutput(
        refund_id=refund_id,
        payment_id=payment_id,
        amount="0.00",  # Would be actual amount
        status="completed",
    )


__all__ = [
    "ChargePaymentInput",
    "PaymentOutput",
    "RefundInput",
    "RefundOutput",
    "charge_payment",
    "refund_payment",
]

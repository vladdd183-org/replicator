"""OrderModule event listeners.

Handles domain events from Order module and cross-module integrations.
"""

import logfire
from litestar.events import listener


@listener("OrderCreated")
async def on_order_created(
    order_id: str,
    user_id: str,
    total_amount: str,
    currency: str,
    item_count: int,
    **kwargs,
) -> None:
    """Handle OrderCreated event.

    Triggers post-order creation workflows:
    - Send confirmation email
    - Update analytics
    - Notify fulfillment system
    """
    logfire.info(
        "📦 Order created event received",
        order_id=order_id,
        user_id=user_id,
        total_amount=total_amount,
        currency=currency,
        item_count=item_count,
    )

    # TODO: Send order confirmation email via NotificationModule
    # TODO: Update user purchase history
    # TODO: Notify fulfillment system


@listener("OrderCancelled")
async def on_order_cancelled(
    order_id: str,
    user_id: str,
    reason: str,
    refund_amount: str,
    **kwargs,
) -> None:
    """Handle OrderCancelled event.

    Triggers cancellation workflows:
    - Send cancellation confirmation
    - Process refund
    - Update inventory
    """
    logfire.info(
        "❌ Order cancelled event received",
        order_id=order_id,
        user_id=user_id,
        reason=reason,
        refund_amount=refund_amount,
    )

    # TODO: Send cancellation email
    # TODO: Trigger refund if not already processed


@listener("OrderSagaCompleted")
async def on_saga_completed(
    saga_id: str,
    order_id: str,
    duration_ms: float,
    **kwargs,
) -> None:
    """Handle OrderSagaCompleted event.

    Records saga metrics for monitoring.
    """
    logfire.info(
        "✅ Order saga completed",
        saga_id=saga_id,
        order_id=order_id,
        duration_ms=duration_ms,
    )


@listener("OrderSagaFailed")
async def on_saga_failed(
    saga_id: str,
    failed_step: str,
    error: str,
    compensations_run: list[str],
    **kwargs,
) -> None:
    """Handle OrderSagaFailed event.

    Alerts and records saga failures.
    """
    logfire.error(
        "❌ Order saga failed",
        saga_id=saga_id,
        failed_step=failed_step,
        error=error,
        compensations_run=compensations_run,
    )

    # TODO: Send alert to operations team
    # TODO: Record failure metrics


# Export listeners for registration
__all__ = [
    "on_order_cancelled",
    "on_order_created",
    "on_saga_completed",
    "on_saga_failed",
]

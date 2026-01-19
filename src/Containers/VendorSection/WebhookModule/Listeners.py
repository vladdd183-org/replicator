"""WebhookModule event listeners for automatic delivery.

Listens to domain events and delivers webhooks to subscribers.
"""

import logfire
from litestar.events import listener

from src.Containers.VendorSection.WebhookModule.Data.Repositories.WebhookRepository import (
    WebhookRepository,
)
from src.Containers.VendorSection.WebhookModule.Tasks.DeliverWebhookTask import (
    DeliverWebhookTask,
    WebhookPayload,
)

__all__ = [
    "on_user_created_webhook",
    "on_user_updated_webhook",
    "on_user_deleted_webhook",
    "on_payment_created_webhook",
    "on_notification_created_webhook",
]

async def _dispatch_to_webhooks(event_type: str, payload: dict) -> None:
    """Find and dispatch to all webhooks subscribed to an event."""
    repository = WebhookRepository()
    task = DeliverWebhookTask()

    webhooks = await repository.get_active_for_event(event_type)

    for webhook in webhooks:
        logfire.info(
            "📤 Dispatching webhook",
            event_type=event_type,
            webhook_id=str(webhook.id),
            url=webhook.url,
        )

        await task.run(
            WebhookPayload(
                webhook_id=webhook.id,
                event_type=event_type,
                payload=payload,
            )
        )


@listener("UserCreated")
async def on_user_created_webhook(
    user_id: str,
    email: str,
    name: str,
    **kwargs,
) -> None:
    """Dispatch user.created webhook."""
    await _dispatch_to_webhooks(
        "user.created",
        {
            "user_id": user_id,
            "email": email,
            "name": name,
        },
    )


@listener("UserUpdated")
async def on_user_updated_webhook(
    user_id: str,
    **kwargs,
) -> None:
    """Dispatch user.updated webhook."""
    await _dispatch_to_webhooks(
        "user.updated",
        {
            "user_id": user_id,
            **kwargs,
        },
    )


@listener("UserDeleted")
async def on_user_deleted_webhook(
    user_id: str,
    **kwargs,
) -> None:
    """Dispatch user.deleted webhook."""
    await _dispatch_to_webhooks(
        "user.deleted",
        {
            "user_id": user_id,
        },
    )


@listener("PaymentCreated")
async def on_payment_created_webhook(
    payment_id: str,
    user_id: str,
    amount: float,
    currency: str,
    status: str,
    **kwargs,
) -> None:
    """Dispatch payment.created webhook."""
    await _dispatch_to_webhooks(
        "payment.created",
        {
            "payment_id": payment_id,
            "user_id": user_id,
            "amount": amount,
            "currency": currency,
            "status": status,
        },
    )


@listener("NotificationCreated")
async def on_notification_created_webhook(
    notification_id: str,
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    **kwargs,
) -> None:
    """Dispatch notification.created webhook."""
    await _dispatch_to_webhooks(
        "notification.created",
        {
            "notification_id": str(notification_id),
            "user_id": str(user_id),
            "type": notification_type,
            "title": title,
            "message": message,
        },
    )

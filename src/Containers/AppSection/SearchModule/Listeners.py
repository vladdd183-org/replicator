"""SearchModule event listeners for automatic indexing.

Listens to domain events and automatically indexes/removes entities.

Note on Task instantiation:
    Litestar @listener doesn't support DI injection directly.
    IndexEntityTask and RemoveFromIndexTask are stateless (no dependencies),
    so direct instantiation is acceptable and intentional.
    For tasks with dependencies, use a different approach (e.g., background workers).
"""

import logfire
from litestar.events import listener

from src.Containers.AppSection.SearchModule.Tasks.IndexEntityTask import (
    IndexableEntity,
    IndexEntityTask,
    RemoveFromIndexTask,
)

__all__ = [
    "on_user_created_index",
    "on_user_updated_index",
    "on_user_deleted_index",
    "on_notification_created_index",
    "on_payment_created_index",
]

# ============== User Events ==============


@listener("UserCreated")
async def on_user_created_index(
    user_id: str,
    email: str,
    name: str,
    **kwargs,
) -> None:
    """Index newly created user."""
    logfire.info("🔍 Indexing new user", user_id=user_id)

    task = IndexEntityTask()
    await task.run(
        IndexableEntity(
            entity_type="User",
            entity_id=user_id,
            title=name,
            content=f"{name} ({email})",
            tags=["user", "active"],
            metadata={"email": email},
        )
    )


@listener("UserUpdated")
async def on_user_updated_index(
    user_id: str,
    **kwargs,
) -> None:
    """Re-index updated user."""
    logfire.info("🔍 Re-indexing user", user_id=user_id)

    # In a real implementation, we would fetch the user data
    # For now, just log the event
    # task = IndexEntityTask()
    # user = await fetch_user(user_id)
    # await task.run(IndexableEntity(...))


@listener("UserDeleted")
async def on_user_deleted_index(
    user_id: str,
    **kwargs,
) -> None:
    """Remove deleted user from index."""
    logfire.info("🗑️ Removing user from index", user_id=user_id)

    task = RemoveFromIndexTask()
    await task.run(("User", user_id))


# ============== Notification Events ==============


@listener("NotificationCreated")
async def on_notification_created_index(
    notification_id: str,
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    **kwargs,
) -> None:
    """Index newly created notification."""
    logfire.info("🔍 Indexing notification", notification_id=notification_id)

    task = IndexEntityTask()
    await task.run(
        IndexableEntity(
            entity_type="Notification",
            entity_id=str(notification_id),
            title=title,
            content=message,
            tags=["notification", notification_type],
            metadata={"user_id": str(user_id), "type": notification_type},
        )
    )


# ============== Payment Events ==============


@listener("PaymentCreated")
async def on_payment_created_index(
    payment_id: str,
    user_id: str,
    amount: float,
    currency: str,
    status: str,
    **kwargs,
) -> None:
    """Index payment."""
    logfire.info("🔍 Indexing payment", payment_id=payment_id)

    task = IndexEntityTask()
    await task.run(
        IndexableEntity(
            entity_type="Payment",
            entity_id=payment_id,
            title=f"Payment {payment_id[:8]}",
            content=f"{amount} {currency} - {status}",
            tags=["payment", status, currency.lower()],
            metadata={
                "user_id": str(user_id),
                "amount": amount,
                "currency": currency,
                "status": status,
            },
        )
    )

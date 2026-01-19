"""User module event listeners.

Listeners handle domain events published via litestar.events.
They run asynchronously after the response is sent.

Events are published as model_dump() dicts from DomainEvent instances.
Listeners receive typed event data via keyword arguments.

WebSocket updates are published via Ship/Infrastructure/Channels.
"""

import logfire
from litestar import Litestar
from litestar.events import listener

from src.Ship.Infrastructure.Channels import publish_to_user_channel


@listener("UserCreated")
async def on_user_created(
    user_id: str,
    email: str,
    app: Litestar | None = None,
    occurred_at: str | None = None,
    **kwargs,
) -> None:
    """Handle UserCreated event.

    Triggered after a new user is successfully created.
    Publishes to WebSocket channel for real-time updates.
    """
    logfire.info(
        "🎉 User created event received",
        user_id=user_id,
        email=email,
        occurred_at=occurred_at,
    )

    # Publish to WebSocket channel
    publish_to_user_channel(app, user_id, "user_created", {"email": email})

    # TODO: Send welcome email via SendWelcomeEmailTask
    # TODO: Create default user settings


@listener("UserDeleted")
async def on_user_deleted(
    user_id: str,
    email: str,
    app: Litestar | None = None,
    occurred_at: str | None = None,
    **kwargs,
) -> None:
    """Handle UserDeleted event.

    Triggered after a user is deleted.
    Publishes to WebSocket channel for real-time updates.
    """
    logfire.info(
        "🗑️ User deleted event received",
        user_id=user_id,
        email=email,
        occurred_at=occurred_at,
    )

    # Publish to WebSocket channel
    publish_to_user_channel(app, user_id, "user_deleted", {"email": email})


@listener("UserUpdated")
async def on_user_updated(
    user_id: str,
    app: Litestar | None = None,
    updated_fields: list[str] | None = None,
    occurred_at: str | None = None,
    **kwargs,
) -> None:
    """Handle UserUpdated event.

    Triggered after a user is updated.
    Publishes to WebSocket channel for real-time updates.
    """
    logfire.info(
        "✏️ User updated event received",
        user_id=user_id,
        updated_fields=updated_fields,
        occurred_at=occurred_at,
    )

    # Publish to WebSocket channel
    publish_to_user_channel(app, user_id, "user_updated", {"updated_fields": updated_fields})


@listener("UserCreated", "UserDeleted", "UserUpdated")
async def on_user_changed(
    user_id: str,
    occurred_at: str | None = None,
    **kwargs,
) -> None:
    """Handle any user change event for audit logging."""
    logfire.info(
        "📝 User change audit",
        user_id=user_id,
        occurred_at=occurred_at,
    )

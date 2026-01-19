"""Webhook model for outgoing webhook registrations."""

from piccolo.columns import JSONB, UUID, Boolean, Integer, Text, Timestamptz, Varchar
from piccolo.columns.defaults.timestamptz import TimestamptzNow
from piccolo.columns.defaults.uuid import UUID4

from src.Ship.Parents.Model import Model


class Webhook(Model):
    """Registered outgoing webhooks.

    Stores webhook subscriptions for event notifications.

    Attributes:
        id: Unique identifier
        user_id: Owner of the webhook (null for system webhooks)
        url: Target URL to deliver webhook to
        secret: Secret for HMAC signature verification
        events: JSON array of events to subscribe to
        is_active: Whether webhook is enabled
        description: Human-readable description
        metadata: Additional configuration
        failure_count: Number of consecutive failures
        last_triggered_at: When last triggered
        created_at: When created
        updated_at: When last modified
    """

    id = UUID(primary_key=True, default=UUID4())
    user_id = UUID(null=True, index=True)
    url = Varchar(length=2000, required=True)
    secret = Varchar(length=255, required=True)  # For HMAC signing
    events = JSONB(required=True)  # ["user.created", "payment.completed"]
    is_active = Boolean(default=True)
    description = Text(null=True)
    metadata = JSONB(null=True)

    # Failure tracking
    failure_count = Integer(default=0)
    last_triggered_at = Timestamptz(null=True)

    created_at = Timestamptz(default=TimestamptzNow())
    updated_at = Timestamptz(default=TimestamptzNow())

    class Meta:
        tablename = "webhooks"

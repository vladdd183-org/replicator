"""WebhookModule domain events."""

from uuid import UUID

from src.Ship.Parents.Event import DomainEvent


class WebhookRegistered(DomainEvent):
    """Emitted when a new webhook is registered."""

    webhook_id: UUID
    url: str
    events: list[str]


class WebhookDelivered(DomainEvent):
    """Emitted when a webhook is successfully delivered."""

    webhook_id: UUID
    delivery_id: UUID
    url: str
    event_type: str
    status_code: int


class WebhookDeliveryFailed(DomainEvent):
    """Emitted when a webhook delivery fails."""

    webhook_id: UUID
    delivery_id: UUID
    url: str
    event_type: str
    error: str
    attempt: int
    will_retry: bool


class IncomingWebhookReceived(DomainEvent):
    """Emitted when an incoming webhook is received."""

    provider: str
    event_type: str
    payload_hash: str


__all__ = [
    "IncomingWebhookReceived",
    "WebhookDelivered",
    "WebhookDeliveryFailed",
    "WebhookRegistered",
]

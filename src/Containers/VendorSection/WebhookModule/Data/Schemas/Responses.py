"""WebhookModule response DTOs."""

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import field_validator

from src.Ship.Core.BaseSchema import EntitySchema


class WebhookResponse(EntitySchema):
    """Response DTO for a webhook."""

    id: UUID
    user_id: UUID | None
    url: str
    events: list[str]
    is_active: bool
    description: str | None
    failure_count: int
    last_triggered_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @field_validator("events", mode="before")
    @classmethod
    def parse_events(cls, v: Any) -> list[str]:
        """Parse events from JSON string if needed."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v or []


class WebhookWithSecretResponse(WebhookResponse):
    """Response DTO for a webhook with secret (only on creation)."""

    secret: str


class WebhooksListResponse(EntitySchema):
    """Response DTO for webhooks list."""

    webhooks: list[WebhookResponse]
    total: int


class WebhookDeliveryResponse(EntitySchema):
    """Response DTO for a webhook delivery."""

    id: UUID
    webhook_id: UUID
    event_type: str
    status: str
    response_status: int | None
    error_message: str | None
    attempt: int
    delivered_at: datetime | None
    created_at: datetime


class WebhookDeliveriesListResponse(EntitySchema):
    """Response DTO for webhook deliveries list."""

    deliveries: list[WebhookDeliveryResponse]
    total: int


class TriggerWebhookResponse(EntitySchema):
    """Response for webhook trigger."""

    delivery_id: UUID
    success: bool
    status_code: int | None
    error: str | None

"""WebhookModule request DTOs.

All Request DTOs are frozen (immutable) for safety.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RegisterWebhookRequest(BaseModel):
    """Request for registering a new webhook."""

    model_config = ConfigDict(frozen=True)

    url: str = Field(..., min_length=1, max_length=2000, description="Webhook endpoint URL")
    events: list[str] = Field(..., min_length=1, description="Events to subscribe to")
    description: str | None = Field(None, max_length=500)
    metadata: dict | None = None


class UpdateWebhookRequest(BaseModel):
    """Request for updating a webhook."""

    model_config = ConfigDict(frozen=True)

    url: str | None = Field(None, min_length=1, max_length=2000)
    events: list[str] | None = None
    is_active: bool | None = None
    description: str | None = None


class TriggerWebhookRequest(BaseModel):
    """Request for manually triggering a webhook."""

    model_config = ConfigDict(frozen=True)

    webhook_id: UUID
    event_type: str = Field(..., min_length=1, max_length=100)
    payload: dict


class IncomingWebhookPayload(BaseModel):
    """Payload for incoming webhooks from external providers."""

    model_config = ConfigDict(frozen=True)

    event_type: str
    data: dict
    timestamp: str | None = None

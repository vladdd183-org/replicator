"""Action for resetting webhook failure count."""

from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel
from returns.result import Failure, Result, Success

from src.Containers.VendorSection.WebhookModule.Data.Repositories.WebhookRepository import (
    WebhookRepository,
)
from src.Containers.VendorSection.WebhookModule.Errors import (
    WebhookError,
    WebhookNotFoundError,
)
from src.Containers.VendorSection.WebhookModule.Models.Webhook import Webhook
from src.Ship.Parents.Action import Action


class ResetWebhookInput(BaseModel):
    """Input for webhook reset."""

    model_config = {"frozen": True}

    webhook_id: UUID


@dataclass
class ResetWebhookAction(Action[ResetWebhookInput, Webhook, WebhookError]):
    """Action for resetting webhook failure count and enabling it."""

    repository: WebhookRepository

    async def run(self, data: ResetWebhookInput) -> Result[Webhook, WebhookError]:
        webhook = await self.repository.reset_failure_count(data.webhook_id)
        if not webhook:
            return Failure(WebhookNotFoundError(webhook_id=data.webhook_id))

        import logfire

        logfire.info(
            "🧹 Webhook reset",
            webhook_id=str(data.webhook_id),
        )

        return Success(webhook)

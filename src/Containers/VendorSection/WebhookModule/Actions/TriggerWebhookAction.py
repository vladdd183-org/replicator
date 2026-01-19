"""Action for triggering a webhook delivery."""

from dataclasses import dataclass

from returns.result import Failure, Result, Success

from src.Containers.VendorSection.WebhookModule.Data.Schemas.Requests import TriggerWebhookRequest
from src.Containers.VendorSection.WebhookModule.Errors import WebhookError, WebhookNotFoundError
from src.Containers.VendorSection.WebhookModule.Tasks.DeliverWebhookTask import (
    DeliverWebhookTask,
    DeliveryResult,
    WebhookPayload,
)
from src.Ship.Parents.Action import Action


@dataclass
class TriggerWebhookAction(Action[TriggerWebhookRequest, DeliveryResult, WebhookError]):
    """Action for manually triggering a webhook delivery."""

    deliver_task: DeliverWebhookTask

    async def run(self, data: TriggerWebhookRequest) -> Result[DeliveryResult, WebhookError]:
        """Trigger webhook delivery."""
        result = await self.deliver_task.run(
            WebhookPayload(
                webhook_id=data.webhook_id,
                event_type=data.event_type,
                payload=data.payload,
            )
        )

        if result.error == "Webhook not found":
            return Failure(WebhookNotFoundError(webhook_id=data.webhook_id))

        return Success(result)

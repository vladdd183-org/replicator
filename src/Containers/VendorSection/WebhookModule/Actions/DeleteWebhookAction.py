"""Action for deleting a webhook."""

from dataclasses import dataclass
from uuid import UUID

from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.VendorSection.WebhookModule.Data.Repositories.WebhookRepository import (
    WebhookRepository,
)
from src.Containers.VendorSection.WebhookModule.Errors import (
    WebhookError,
    WebhookNotFoundError,
)


@dataclass
class DeleteWebhookInput:
    """Input for webhook deletion."""
    
    webhook_id: UUID


@dataclass
class DeleteWebhookAction(Action[DeleteWebhookInput, None, WebhookError]):
    """Action for deleting a webhook."""
    
    repository: WebhookRepository
    
    async def run(self, data: DeleteWebhookInput) -> Result[None, WebhookError]:
        webhook = await self.repository.get(data.webhook_id)
        if not webhook:
            return Failure(WebhookNotFoundError(webhook_id=data.webhook_id))
        
        await self.repository.delete(webhook)
        
        import logfire
        logfire.info(
            "🗑️ Webhook deleted",
            webhook_id=str(data.webhook_id),
        )
        
        return Success(None)

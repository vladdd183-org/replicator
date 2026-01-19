"""Action for toggling webhook active state."""

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
from src.Containers.VendorSection.WebhookModule.Models.Webhook import Webhook


@dataclass
class ToggleWebhookInput:
    """Input for webhook toggle."""
    
    webhook_id: UUID
    is_active: bool


@dataclass
class ToggleWebhookAction(Action[ToggleWebhookInput, Webhook, WebhookError]):
    """Action for enabling or disabling a webhook."""
    
    repository: WebhookRepository
    
    async def run(self, data: ToggleWebhookInput) -> Result[Webhook, WebhookError]:
        webhook = await self.repository.toggle_active(data.webhook_id, data.is_active)
        if not webhook:
            return Failure(WebhookNotFoundError(webhook_id=data.webhook_id))
        
        import logfire
        logfire.info(
            "🪝 Webhook toggled",
            webhook_id=str(data.webhook_id),
            is_active=data.is_active,
        )
        
        return Success(webhook)

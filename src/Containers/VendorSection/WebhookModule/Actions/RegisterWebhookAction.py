"""Action for registering a new webhook."""

from dataclasses import dataclass
from uuid import UUID

from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.VendorSection.WebhookModule.Data.Schemas.Requests import RegisterWebhookRequest
from src.Containers.VendorSection.WebhookModule.Data.Repositories.WebhookRepository import WebhookRepository
from src.Containers.VendorSection.WebhookModule.Errors import WebhookError, WebhookUrlInvalidError
from src.Containers.VendorSection.WebhookModule.Models.Webhook import Webhook


@dataclass
class RegisterWebhookInput:
    """Input for webhook registration."""
    
    request: RegisterWebhookRequest
    user_id: UUID | None = None


@dataclass
class RegisterWebhookAction(Action[RegisterWebhookInput, Webhook, WebhookError]):
    """Action for registering a new outgoing webhook."""
    
    repository: WebhookRepository
    
    async def run(self, data: RegisterWebhookInput) -> Result[Webhook, WebhookError]:
        """Register a new webhook."""
        # Validate URL
        url = data.request.url
        if not url.startswith(("http://", "https://")):
            return Failure(WebhookUrlInvalidError(url=url))
        
        # Validate events
        valid_events = {
            "user.created", "user.updated", "user.deleted",
            "payment.created", "payment.completed", "payment.failed",
            "notification.created",
            "*",  # Wildcard for all events
        }
        
        for event in data.request.events:
            if event not in valid_events and not event.startswith("custom."):
                # Allow custom.* events
                pass
        
        # Create webhook
        webhook = await self.repository.create_webhook(
            url=url,
            events=data.request.events,
            user_id=data.user_id,
            description=data.request.description,
            metadata=data.request.metadata,
        )
        
        import logfire
        logfire.info(
            "🪝 Webhook registered",
            webhook_id=str(webhook.id),
            url=url,
            events=data.request.events,
        )
        
        return Success(webhook)




"""ListWebhooksQuery - list webhooks with optional user filter."""

from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.Containers.VendorSection.WebhookModule.Data.Repositories.WebhookRepository import (
    WebhookRepository,
)
from src.Containers.VendorSection.WebhookModule.Models.Webhook import Webhook
from src.Ship.Parents.Query import Query


class ListWebhooksQueryInput(BaseModel):
    """Input for list webhooks query."""

    model_config = ConfigDict(frozen=True)

    user_id: UUID | None = None


@dataclass(frozen=True)
class WebhooksListResult:
    """Result of webhooks list query."""

    webhooks: list[Webhook]
    total: int


class ListWebhooksQuery(Query[ListWebhooksQueryInput, WebhooksListResult]):
    """CQRS Query: List webhooks with optional user filter."""

    def __init__(self, repository: WebhookRepository) -> None:
        self.repository = repository

    async def execute(self, input: ListWebhooksQueryInput) -> WebhooksListResult:
        if input.user_id:
            webhooks = await self.repository.get_by_user(input.user_id)
        else:
            webhooks = await self.repository.get_all()

        return WebhooksListResult(webhooks=webhooks, total=len(webhooks))

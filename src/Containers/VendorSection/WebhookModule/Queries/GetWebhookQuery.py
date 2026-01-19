"""GetWebhookQuery - fetch webhook by ID."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.Containers.VendorSection.WebhookModule.Data.Repositories.WebhookRepository import (
    WebhookRepository,
)
from src.Containers.VendorSection.WebhookModule.Models.Webhook import Webhook
from src.Ship.Parents.Query import Query


class GetWebhookQueryInput(BaseModel):
    """Input for get webhook query."""

    model_config = ConfigDict(frozen=True)

    webhook_id: UUID


class GetWebhookQuery(Query[GetWebhookQueryInput, Webhook | None]):
    """CQRS Query: Get webhook by ID."""

    def __init__(self, repository: WebhookRepository) -> None:
        self.repository = repository

    async def execute(self, input: GetWebhookQueryInput) -> Webhook | None:
        return await self.repository.get(input.webhook_id)

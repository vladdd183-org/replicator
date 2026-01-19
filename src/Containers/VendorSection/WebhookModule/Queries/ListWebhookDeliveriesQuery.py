"""ListWebhookDeliveriesQuery - list deliveries for a webhook."""

from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.Containers.VendorSection.WebhookModule.Data.Repositories.WebhookRepository import (
    WebhookDeliveryRepository,
)
from src.Containers.VendorSection.WebhookModule.Models.WebhookDelivery import WebhookDelivery
from src.Ship.Parents.Query import Query


class ListWebhookDeliveriesQueryInput(BaseModel):
    """Input for list webhook deliveries query."""

    model_config = ConfigDict(frozen=True)

    webhook_id: UUID
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


@dataclass(frozen=True)
class WebhookDeliveriesListResult:
    """Result of webhook deliveries list query."""

    deliveries: list[WebhookDelivery]
    total: int


class ListWebhookDeliveriesQuery(
    Query[ListWebhookDeliveriesQueryInput, WebhookDeliveriesListResult]
):
    """CQRS Query: List deliveries for a webhook."""

    def __init__(self, repository: WebhookDeliveryRepository) -> None:
        self.repository = repository

    async def execute(self, input: ListWebhookDeliveriesQueryInput) -> WebhookDeliveriesListResult:
        deliveries = await self.repository.get_by_webhook(
            webhook_id=input.webhook_id,
            limit=input.limit,
            offset=input.offset,
        )

        return WebhookDeliveriesListResult(
            deliveries=deliveries,
            total=len(deliveries),
        )

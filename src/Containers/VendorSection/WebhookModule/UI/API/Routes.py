"""WebhookModule API routes."""

from dishka.integrations.litestar import DishkaRouter

from src.Containers.VendorSection.WebhookModule.UI.API.Controllers.WebhookController import (
    IncomingWebhookController,
    WebhookController,
)

webhook_router = DishkaRouter(
    path="/api/v1",
    route_handlers=[
        WebhookController,
        IncomingWebhookController,
    ],
)

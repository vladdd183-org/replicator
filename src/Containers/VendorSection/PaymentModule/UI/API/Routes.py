"""Payment module routes configuration.

Uses DishkaRouter for automatic dependency injection.
"""

from dishka.integrations.litestar import DishkaRouter

from src.Containers.VendorSection.PaymentModule.UI.API.Controllers.PaymentController import (
    PaymentController,
)

# Payment router - groups all payment-related endpoints under /api/v1
payment_router = DishkaRouter(
    path="/api/v1",
    route_handlers=[
        PaymentController,
    ],
)

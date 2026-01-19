"""Email module routes configuration.

Uses DishkaRouter for automatic dependency injection.
"""

from dishka.integrations.litestar import DishkaRouter

from src.Containers.VendorSection.EmailModule.UI.API.Controllers.EmailController import (
    EmailController,
)


# Email router - groups all email-related endpoints under /api/v1
email_router = DishkaRouter(
    path="/api/v1",
    route_handlers=[
        EmailController,
    ],
)




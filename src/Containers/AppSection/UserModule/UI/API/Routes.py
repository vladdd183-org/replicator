"""User module routes configuration.

Uses DishkaRouter for automatic dependency injection.
"""

from dishka.integrations.litestar import DishkaRouter

from src.Containers.AppSection.UserModule.UI.API.Controllers.UserController import UserController
from src.Containers.AppSection.UserModule.UI.API.Controllers.AuthController import AuthController


# User router - groups all user-related endpoints under /api/v1
# DishkaRouter automatically applies @inject to all handlers
user_router = DishkaRouter(
    path="/api/v1",
    route_handlers=[
        UserController,
        AuthController,
    ],
)

"""Order module routes."""

from dishka.integrations.litestar import DishkaRouter

from src.Containers.AppSection.OrderModule.UI.API.Controllers.OrderController import OrderController

order_router = DishkaRouter(
    path="/api/v1",
    route_handlers=[OrderController],
)


__all__ = ["order_router"]

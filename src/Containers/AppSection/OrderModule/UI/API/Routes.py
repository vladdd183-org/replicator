"""Order module routes."""

from litestar import Router

from src.Containers.AppSection.OrderModule.UI.API.Controllers.OrderController import OrderController


order_router = Router(
    path="/api/v1",
    route_handlers=[OrderController],
)


__all__ = ["order_router"]

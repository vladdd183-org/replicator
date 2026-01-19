"""SearchModule API routes."""

from dishka.integrations.litestar import DishkaRouter

from src.Containers.AppSection.SearchModule.UI.API.Controllers.SearchController import (
    SearchController,
)

search_router = DishkaRouter(
    path="/api/v1",
    route_handlers=[
        SearchController,
    ],
)




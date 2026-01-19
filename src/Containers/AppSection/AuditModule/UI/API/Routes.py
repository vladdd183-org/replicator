"""AuditModule API routes."""

from dishka.integrations.litestar import DishkaRouter

from src.Containers.AppSection.AuditModule.UI.API.Controllers.AuditController import (
    AuditController,
)

audit_router = DishkaRouter(
    path="/api/v1",
    route_handlers=[
        AuditController,
    ],
)




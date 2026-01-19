"""Health check endpoint for monitoring.

Provides /health and /ready endpoints for container orchestration.
"""

from datetime import datetime, timezone
from typing import Literal

from litestar import Controller, get, Response
from litestar.status_codes import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE
from pydantic import BaseModel

from piccolo.engine import engine_finder


class HealthStatus(BaseModel):
    """Health check response.
    
    Attributes:
        status: Health status (healthy/unhealthy)
        timestamp: Current timestamp
        version: Application version
        checks: Individual component checks
    """
    
    status: Literal["healthy", "unhealthy"]
    timestamp: datetime
    version: str
    checks: dict[str, bool] = {}


class HealthController(Controller):
    """Health check endpoints for monitoring.
    
    Provides:
    - GET /health - Basic liveness probe
    - GET /ready - Readiness probe with dependency checks
    """
    
    path = "/health"
    tags = ["Health"]
    
    @get("/")
    async def liveness(self) -> dict:
        """Basic liveness probe.
        
        Returns 200 if the application is running.
        Used by container orchestration for restart decisions.
        """
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    @get("/ready")
    async def readiness(self) -> Response[HealthStatus]:
        """Readiness probe with dependency checks.
        
        Checks:
        - Database connectivity
        
        Returns 200 if all dependencies are ready, 503 otherwise.
        Used by load balancers for traffic routing decisions.
        """
        from src.Ship.Configs import get_settings
        
        settings = get_settings()
        checks: dict[str, bool] = {}
        
        # Check database connectivity
        try:
            engine = engine_finder()
            if engine:
                # Simple query to verify connection
                from src.Containers.AppSection.UserModule.Models.User import AppUser
                await AppUser.count()
                checks["database"] = True
            else:
                checks["database"] = False
        except Exception:
            checks["database"] = False
        
        # Determine overall status
        all_healthy = all(checks.values())
        status = "healthy" if all_healthy else "unhealthy"
        status_code = HTTP_200_OK if all_healthy else HTTP_503_SERVICE_UNAVAILABLE
        
        response = HealthStatus(
            status=status,
            timestamp=datetime.now(timezone.utc),
            version=settings.app_version,
            checks=checks,
        )
        
        return Response(content=response, status_code=status_code)


# Export controller for registration in App.py
health_controller = HealthController




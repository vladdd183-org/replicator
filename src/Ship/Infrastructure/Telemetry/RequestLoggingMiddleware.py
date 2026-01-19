"""Request logging middleware.

Logs all HTTP requests with timing and status information.
"""

import time
from typing import TYPE_CHECKING

from litestar.middleware import MiddlewareProtocol

from src.Ship.Infrastructure.Telemetry.Logfire import log_request

if TYPE_CHECKING:
    from litestar.types import ASGIApp, Receive, Scope, Send


class RequestLoggingMiddleware(MiddlewareProtocol):
    """Middleware to log all HTTP requests."""
    
    def __init__(self, app: "ASGIApp") -> None:
        self.app = app
    
    async def __call__(
        self, scope: "Scope", receive: "Receive", send: "Send"
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.perf_counter()
        status_code = 500  # Default in case of exception
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            method = scope.get("method", "UNKNOWN")
            path = scope.get("path", "/")
            log_request(method, path, status_code, duration_ms)


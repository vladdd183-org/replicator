"""Audit Middleware for HTTP request logging.

Automatically logs all HTTP requests with:
- Request details (method, path, headers)
- Response status
- Duration
- Actor information (from JWT)
"""

import time
from typing import TYPE_CHECKING
from uuid import UUID

from litestar import Request, Response
from litestar.middleware import AbstractMiddleware
from litestar.types import ASGIApp, Receive, Scope, Send

from src.Ship.Auth.JWT import get_jwt_service
from src.Containers.AppSection.AuditModule.Models.AuditLog import AuditLog

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection


class AuditMiddleware(AbstractMiddleware):
    """Middleware that logs all HTTP requests to audit trail.
    
    Captures:
    - Request method, path, query params
    - Client IP address
    - User agent
    - Actor ID (from JWT token)
    - Response status code
    - Request duration
    
    Excluded paths:
    - /health, /health/ready (health checks)
    - /api/docs (documentation)
    - /static (static files)
    - /api/v1/audit (to avoid recursive logging)
    """
    
    scopes = {"http"}
    exclude = [
        "/health",
        "/api/docs",
        "/static",
        "/api/v1/audit",
        "/schema",
    ]
    
    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """Process request and log to audit trail."""
        start_time = time.perf_counter()
        
        # Extract request info
        path = scope.get("path", "")
        method = scope.get("method", "")
        
        # Skip excluded paths
        if any(path.startswith(exc) for exc in self.exclude):
            await self.app(scope, receive, send)
            return
        
        # Extract headers
        headers = dict(scope.get("headers", []))
        
        # Get client IP
        client = scope.get("client")
        ip_address = client[0] if client else None
        
        # Get user agent
        user_agent = headers.get(b"user-agent", b"").decode("utf-8", errors="ignore")
        
        # Try to extract actor from JWT
        actor_id: UUID | None = None
        actor_email: str | None = None
        
        auth_header = headers.get(b"authorization", b"").decode("utf-8", errors="ignore")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                jwt_service = get_jwt_service()
                payload = jwt_service.verify_token(token)
                if payload:
                    actor_id = payload.sub
                    actor_email = payload.email
            except Exception:
                pass
        
        # Capture response status
        status_code: int | None = None
        
        async def send_wrapper(message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status")
            await send(message)
        
        # Process request
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Determine action based on method
            action = f"http_{method.lower()}"
            
            # Create audit log (fire and forget)
            try:
                audit_log = AuditLog(
                    actor_id=actor_id,
                    actor_email=actor_email,
                    action=action,
                    entity_type="http_request",
                    entity_id=None,
                    ip_address=ip_address,
                    user_agent=user_agent[:500] if user_agent else None,
                    endpoint=path,
                    http_method=method,
                    status_code=str(status_code) if status_code else None,
                    duration_ms=f"{duration_ms:.2f}",
                    metadata={
                        "query_string": scope.get("query_string", b"").decode("utf-8", errors="ignore"),
                    } if scope.get("query_string") else None,
                )
                await audit_log.save()
            except Exception:
                # Don't fail request if audit logging fails
                pass




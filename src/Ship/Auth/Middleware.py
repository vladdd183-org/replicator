"""Authentication Middleware for Litestar.

Extracts and validates JWT tokens from requests.
"""

from uuid import UUID
from dataclasses import dataclass
from typing import TYPE_CHECKING

from litestar.middleware import MiddlewareProtocol
from litestar.connection import Request

if TYPE_CHECKING:
    from litestar.types import ASGIApp, Receive, Scope, Send

from src.Ship.Auth.JWT import TokenPayload, get_jwt_service


@dataclass
class AuthUser:
    """Authenticated user context.
    
    Stored in request state after successful authentication.
    
    Attributes:
        id: User UUID
        email: User email
        token_payload: Full token payload
    """
    
    id: UUID
    email: str
    token_payload: TokenPayload


class AuthenticationMiddleware(MiddlewareProtocol):
    """Middleware that extracts JWT from Authorization header.
    
    Sets `request.state.auth_user` if valid token is present.
    Does not block requests without tokens - use guards for that.
    Uses singleton JWTService via get_jwt_service().
    
    Example header:
        Authorization: Bearer <token>
    """
    
    def __init__(self, app: "ASGIApp") -> None:
        """Initialize middleware."""
        self.app = app
        self.jwt_service = get_jwt_service()
    
    async def __call__(
        self,
        scope: "Scope",
        receive: "Receive",
        send: "Send",
    ) -> None:
        """Process request and extract authentication."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Initialize auth_user as None
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["auth_user"] = None
        
        # Get Authorization header
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()
        
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            payload = self.jwt_service.verify_token(token)
            
            if payload:
                scope["state"]["auth_user"] = AuthUser(
                    id=payload.sub,
                    email=payload.email,
                    token_payload=payload,
                )
        
        await self.app(scope, receive, send)


def get_auth_user_from_request(request: Request) -> AuthUser | None:
    """Get authenticated user from request state.
    
    Helper function for use in handlers and guards.
    
    Args:
        request: Litestar Request object
        
    Returns:
        AuthUser if authenticated, None otherwise
    """
    return getattr(request.state, "auth_user", None)


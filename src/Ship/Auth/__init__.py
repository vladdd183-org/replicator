"""Authentication module for Ship layer.

Provides JWT-based authentication, middleware, and guards.
"""

from src.Ship.Auth.JWT import JWTService, TokenPayload
from src.Ship.Auth.Middleware import AuthenticationMiddleware
from src.Ship.Auth.Guards import auth_guard, optional_auth_guard, CurrentUser
from src.Ship.Auth.Dependencies import get_current_user, require_admin

__all__ = [
    "JWTService",
    "TokenPayload",
    "AuthenticationMiddleware",
    "auth_guard",
    "optional_auth_guard",
    "CurrentUser",
    "get_current_user",
    "require_admin",
]

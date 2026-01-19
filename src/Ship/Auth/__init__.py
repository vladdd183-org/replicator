"""Authentication module for Ship layer.

Provides JWT-based authentication, middleware, and guards.
"""

from src.Ship.Auth.JWT import JWTService, TokenPayload
from src.Ship.Auth.Middleware import AuthenticationMiddleware
from src.Ship.Auth.Guards import auth_guard, optional_auth_guard, CurrentUser

__all__ = [
    "JWTService",
    "TokenPayload",
    "AuthenticationMiddleware",
    "auth_guard",
    "optional_auth_guard",
    "CurrentUser",
]




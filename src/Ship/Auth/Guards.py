"""Authentication Guards for route protection.

Provides dependency injection for authenticated user and route guards.
"""

from uuid import UUID
from typing import Annotated

from litestar import Request
from litestar.exceptions import NotAuthorizedException
from litestar.params import Dependency

from src.Ship.Auth.Middleware import AuthUser, get_auth_user_from_request


async def auth_guard(request: Request) -> AuthUser:
    """Guard that requires authentication.
    
    Use as a dependency to protect routes.
    Raises NotAuthorizedException if not authenticated.
    
    Example:
        @get("/protected")
        async def protected_route(
            current_user: CurrentUser,
        ) -> dict:
            return {"user_id": str(current_user.id)}
    
    Args:
        request: Litestar Request
        
    Returns:
        Authenticated user
        
    Raises:
        NotAuthorizedException: If not authenticated
    """
    auth_user = get_auth_user_from_request(request)
    
    if auth_user is None:
        raise NotAuthorizedException(
            detail="Authentication required",
            extra={"code": "AUTH_REQUIRED"},
        )
    
    return auth_user


async def optional_auth_guard(request: Request) -> AuthUser | None:
    """Guard that optionally extracts authentication.
    
    Does not raise exception if not authenticated.
    Useful for routes that work both authenticated and anonymously.
    
    Example:
        @get("/feed")
        async def get_feed(
            current_user: OptionalUser,
        ) -> dict:
            if current_user:
                return {"personalized": True}
            return {"personalized": False}
    
    Args:
        request: Litestar Request
        
    Returns:
        AuthUser if authenticated, None otherwise
    """
    return get_auth_user_from_request(request)


# Type aliases for dependency injection with guards
# CurrentUser - requires authentication (use with dependencies={"current_user": auth_guard})
# For direct injection, use Provide wrapper
CurrentUser = Annotated[AuthUser, Dependency(skip_validation=True)]
OptionalUser = Annotated[AuthUser | None, Dependency(skip_validation=True)]


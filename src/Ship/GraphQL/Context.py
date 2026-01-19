"""GraphQL context setup for Litestar integration.

Provides context getter for GraphQL resolvers with access to request and DI container.
"""

from typing import Any

from litestar import Request


async def get_graphql_context(request: Request) -> dict[str, Any]:
    """Get GraphQL context with request for DI access.
    
    This context is available in resolvers via info.context.
    With dishka-strawberry, you can use FromDishka directly in resolver parameters.
    
    Args:
        request: Litestar Request object
        
    Returns:
        Context dictionary with request and useful utilities
        
    Example usage in resolver:
        @strawberry.field
        def current_user(self, info: strawberry.Info) -> User:
            request = info.context["request"]
            # Access request headers, state, etc.
    """
    return {
        "request": request,
        # Add more context as needed:
        # "user": getattr(request.state, "user", None),
        # "locale": request.headers.get("Accept-Language", "en"),
    }




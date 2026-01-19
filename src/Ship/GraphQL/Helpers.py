"""GraphQL helper functions for reducing boilerplate.

Provides utilities for:
- Dependency injection in resolvers via get_dependency()
- Result mapping to GraphQL types

NOTE: dishka-strawberry library requires FastAPI and cannot be used with Litestar.
Use get_dependency() helper instead for DI in resolvers.
"""

from typing import TypeVar, Type
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import strawberry

T = TypeVar("T")


async def get_dependency(info: strawberry.Info, dep_type: Type[T]) -> T:
    """Get dependency from Dishka container in GraphQL context.
    
    This is the recommended way to get dependencies in Strawberry resolvers
    when using Litestar (dishka-strawberry requires FastAPI).
    
    Note: This uses the request-scoped container context that Dishka creates
    automatically for each HTTP request via LitestarProvider.
    
    Args:
        info: Strawberry info context
        dep_type: Type of dependency to resolve
        
    Returns:
        Resolved dependency instance
        
    Example:
        @strawberry.field
        async def user(self, id: UUID, info: strawberry.Info) -> UserType | None:
            query = await get_dependency(info, GetUserQuery)
            user = await query.execute(id)
            return UserType.from_entity(user) if user else None
    """
    container = info.context["request"].state.dishka_container
    return await container.get(dep_type)


@asynccontextmanager
async def get_container_context(info: strawberry.Info) -> AsyncGenerator[object, None]:
    """Get Dishka container context manager for multiple dependencies.
    
    Use this when you need to resolve multiple dependencies in one resolver.
    Properly manages container lifecycle.
    
    Args:
        info: Strawberry info context
        
    Yields:
        Request-scoped container context
        
    Example:
        @strawberry.field
        async def complex_query(self, info: strawberry.Info) -> SomeType:
            async with get_container_context(info) as container:
                query1 = await container.get(Query1)
                query2 = await container.get(Query2)
                # use both queries...
    """
    container = info.context["request"].state.dishka_container
    async with container() as request_container:
        yield request_container

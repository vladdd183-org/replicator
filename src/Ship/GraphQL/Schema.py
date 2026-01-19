"""Root GraphQL Schema.

Uses manual dependency injection via get_dependency helper.
"""

import strawberry

from src.Containers.AppSection.UserModule.UI.GraphQL.Resolvers import (
    UserQuery,
    UserMutation,
)
# Re-export context getter for convenience
from src.Ship.GraphQL.Context import get_graphql_context


@strawberry.type
class Query(UserQuery):
    """Root GraphQL Query.

    Inherits from module-specific queries.
    """

    pass


@strawberry.type
class Mutation(UserMutation):
    """Root GraphQL Mutation.

    Inherits from module-specific mutations.
    """

    pass


# Create schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
)


__all__ = ["schema", "get_graphql_context", "Query", "Mutation"]

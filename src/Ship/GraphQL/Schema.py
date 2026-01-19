"""Base GraphQL types for Ship layer.

Ship provides base types and helpers. Actual schema assembly
with Container resolvers happens in App.py to maintain proper
architecture layering (Ship → Containers is forbidden).

Re-exports context getter for convenience.
"""

# Re-export context getter for convenience
from src.Ship.GraphQL.Context import get_graphql_context


__all__ = ["get_graphql_context"]

"""User module CQRS queries.

Queries are read-only operations optimized for data retrieval.
"""

from src.Containers.AppSection.UserModule.Queries.GetUserQuery import (
    GetUserQuery,
    GetUserQueryInput,
)
from src.Containers.AppSection.UserModule.Queries.ListUsersQuery import (
    ListUsersQuery,
    ListUsersQueryInput,
    ListUsersQueryOutput,
)

__all__ = [
    "GetUserQuery",
    "GetUserQueryInput",
    "ListUsersQuery",
    "ListUsersQueryInput",
    "ListUsersQueryOutput",
]

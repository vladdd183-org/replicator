"""GraphQL types for UserModule.

Uses strawberry.experimental.pydantic for automatic type generation from Pydantic models.
This eliminates duplication between Pydantic responses and GraphQL types.
"""

import strawberry
from strawberry.experimental.pydantic import type as pydantic_type, input as pydantic_input

from src.Containers.AppSection.UserModule.Data.Schemas.Responses import (
    UserResponse,
    UserListResponse,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import (
    CreateUserRequest,
    UpdateUserRequest,
)


# Auto-generate GraphQL types from Pydantic models
@pydantic_type(model=UserResponse, all_fields=True)
class UserType:
    """GraphQL type for User - auto-generated from UserResponse."""
    pass


@pydantic_type(model=UserListResponse, all_fields=True)
class UserListType:
    """GraphQL type for paginated user list - auto-generated from UserListResponse."""
    pass


# Input types - auto-generated from Pydantic request models
@pydantic_input(model=CreateUserRequest, all_fields=True)
class CreateUserInput:
    """Input for creating a user - auto-generated from CreateUserRequest."""
    pass


@pydantic_input(model=UpdateUserRequest, all_fields=True)
class UpdateUserInput:
    """Input for updating a user - auto-generated from UpdateUserRequest."""
    pass


# Error and payload types (GraphQL-specific, not from Pydantic)
@strawberry.type
class UserError:
    """GraphQL error type."""
    message: str
    code: str


@strawberry.type
class CreateUserPayload:
    """Payload for createUser mutation."""
    user: UserType | None = None
    error: UserError | None = None


@strawberry.type
class DeleteUserPayload:
    """Payload for deleteUser mutation."""
    success: bool
    error: UserError | None = None

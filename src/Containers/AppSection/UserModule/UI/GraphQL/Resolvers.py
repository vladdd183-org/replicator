"""GraphQL resolvers for UserModule.

Uses get_dependency helper for DI in resolvers.
According to CQRS:
- Mutations use Actions (write operations)
- Queries use Query classes (read operations)

NOTE: dishka-strawberry library requires FastAPI, so we use
get_dependency() helper instead for Litestar compatibility.
"""

from uuid import UUID

import strawberry
from returns.result import Failure, Success

from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Actions.DeleteUserAction import DeleteUserAction
from src.Containers.AppSection.UserModule.Data.Schemas.Responses import (
    UserListResponse,
    UserResponse,
)
from src.Containers.AppSection.UserModule.Queries.GetUserQuery import (
    GetUserQuery,
    GetUserQueryInput,
)
from src.Containers.AppSection.UserModule.Queries.ListUsersQuery import (
    ListUsersQuery,
    ListUsersQueryInput,
)
from src.Containers.AppSection.UserModule.UI.GraphQL.Types import (
    CreateUserInput,
    CreateUserPayload,
    DeleteUserPayload,
    UserListType,
    UserType,
)
from src.Containers.AppSection.UserModule.UI.GraphQL.Types import (
    UserError as UserErrorType,
)
from src.Ship.GraphQL.Helpers import get_dependency


def _user_to_graphql(user) -> UserType:
    """Convert User entity to GraphQL UserType via Pydantic."""
    response = UserResponse.from_entity(user)
    return UserType.from_pydantic(response)


@strawberry.type
class UserQuery:
    """GraphQL queries for users.

    Uses get_dependency helper for DI.
    Uses CQRS Query classes for read operations.
    """

    @strawberry.field
    async def user(
        self,
        id: UUID,
        info: strawberry.Info,
    ) -> UserType | None:
        """Get user by ID."""
        query = await get_dependency(info, GetUserQuery)
        user = await query.execute(GetUserQueryInput(user_id=id))
        return _user_to_graphql(user) if user else None

    @strawberry.field
    async def users(
        self,
        info: strawberry.Info,
        limit: int = 20,
        offset: int = 0,
        active_only: bool = False,
    ) -> UserListType:
        """List users with pagination."""
        query = await get_dependency(info, ListUsersQuery)

        result = await query.execute(
            ListUsersQueryInput(
                limit=limit,
                offset=offset,
                active_only=active_only,
            )
        )

        # Convert to Pydantic then to Strawberry
        response = UserListResponse(
            users=[UserResponse.from_entity(u) for u in result.users],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )
        return UserListType.from_pydantic(response)


@strawberry.type
class UserMutation:
    """GraphQL mutations for users.

    Uses get_dependency helper for DI.
    Uses Actions for write operations (CQRS command side).
    """

    @strawberry.mutation
    async def create_user(
        self,
        input: CreateUserInput,
        info: strawberry.Info,
    ) -> CreateUserPayload:
        """Create a new user."""
        action = await get_dependency(info, CreateUserAction)

        # Convert Strawberry input to Pydantic
        request = input.to_pydantic()
        result = await action.run(request)

        match result:
            case Success(user):
                return CreateUserPayload(user=_user_to_graphql(user))
            case Failure(error):
                return CreateUserPayload(
                    error=UserErrorType(message=error.message, code=error.code)
                )

    @strawberry.mutation
    async def delete_user(
        self,
        id: UUID,
        info: strawberry.Info,
    ) -> DeleteUserPayload:
        """Delete a user by ID."""
        action = await get_dependency(info, DeleteUserAction)
        result = await action.run(id)

        match result:
            case Success(_):
                return DeleteUserPayload(success=True)
            case Failure(error):
                return DeleteUserPayload(
                    success=False, error=UserErrorType(message=error.message, code=error.code)
                )

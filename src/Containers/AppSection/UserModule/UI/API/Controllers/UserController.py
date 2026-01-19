"""User HTTP API Controller.

Uses DishkaRouter - no need for @inject decorator.
All endpoints use @result_handler for consistent Result -> Response conversion.

According to documentation:
- Controllers call action.run() for write operations
- Controllers call query.execute() for read operations (CQRS)
"""

from uuid import UUID

from dishka.integrations.litestar import FromDishka
from litestar import Controller, delete, get, patch, post
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from returns.result import Result

from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Actions.DeleteUserAction import DeleteUserAction
from src.Containers.AppSection.UserModule.Actions.UpdateUserAction import (
    UpdateUserAction,
    UpdateUserInput,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import (
    CreateUserRequest,
    UpdateUserRequest,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Responses import (
    UserListResponse,
    UserResponse,
)
from src.Containers.AppSection.UserModule.Errors import UserError, UserNotFoundError
from src.Containers.AppSection.UserModule.Models.User import AppUser
from src.Containers.AppSection.UserModule.Queries.GetUserQuery import (
    GetUserQuery,
    GetUserQueryInput,
)
from src.Containers.AppSection.UserModule.Queries.ListUsersQuery import (
    ListUsersQuery,
    ListUsersQueryInput,
)
from src.Ship.Core.Errors import DomainException
from src.Ship.Decorators.result_handler import result_handler


class UserController(Controller):
    """HTTP API controller for User operations.

    Handles all user-related HTTP endpoints.
    Uses Actions for write operations and Queries for read operations (CQRS).
    Uses result_handler for response formatting.

    Note: @inject is not needed when using DishkaRouter.
    """

    path = "/users"
    tags = ["Users"]

    @post("/")
    @result_handler(UserResponse, success_status=HTTP_201_CREATED)
    async def create_user(
        self,
        data: CreateUserRequest,
        action: FromDishka[CreateUserAction],
    ) -> Result[AppUser, UserError]:
        """Create a new user.

        Args:
            data: CreateUserRequest with user data
            action: Injected CreateUserAction

        Returns:
            Created user as UserResponse (201) or error
        """
        return await action.run(data)

    @get("/{user_id:uuid}")
    async def get_user(
        self,
        user_id: UUID,
        query: FromDishka[GetUserQuery],
    ) -> UserResponse:
        """Get user by ID.

        Args:
            user_id: User UUID
            query: Injected GetUserQuery

        Returns:
            User as UserResponse (200) or NotFound error (404)
        """
        user = await query.execute(GetUserQueryInput(user_id=user_id))
        if user is None:
            raise DomainException(UserNotFoundError(user_id=user_id))

        return UserResponse.from_entity(user)

    @get("/")
    async def list_users(
        self,
        query: FromDishka[ListUsersQuery],
        limit: int = 20,
        offset: int = 0,
        active_only: bool = False,
    ) -> UserListResponse:
        """List users with pagination.

        Uses CQRS Query directly for read operations (no Action wrapper).

        Args:
            query: Injected ListUsersQuery
            limit: Maximum number of users to return (default: 20)
            offset: Number of users to skip (default: 0)
            active_only: If True, only return active users

        Returns:
            UserListResponse with users and pagination info
        """
        result = await query.execute(
            ListUsersQueryInput(
                limit=limit,
                offset=offset,
                active_only=active_only,
            )
        )

        return UserListResponse(
            users=[UserResponse.from_entity(u) for u in result.users],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )

    @patch("/{user_id:uuid}")
    @result_handler(UserResponse, success_status=HTTP_200_OK)
    async def update_user(
        self,
        user_id: UUID,
        data: UpdateUserRequest,
        action: FromDishka[UpdateUserAction],
    ) -> Result[AppUser, UserError]:
        """Update user by ID.

        Args:
            user_id: User UUID to update
            data: UpdateUserRequest with fields to update
            action: Injected UpdateUserAction

        Returns:
            Updated user as UserResponse (200) or error
        """
        return await action.run(UpdateUserInput(user_id=user_id, data=data))

    # Set status_code=200 to allow returning Response object from result_handler
    # result_handler will set actual status to 204
    @delete("/{user_id:uuid}", status_code=HTTP_200_OK)
    @result_handler(None, success_status=HTTP_204_NO_CONTENT)
    async def delete_user(
        self,
        user_id: UUID,
        action: FromDishka[DeleteUserAction],
    ) -> Result[None, UserError]:
        """Delete user by ID (soft delete).

        Args:
            user_id: User UUID to delete
            action: Injected DeleteUserAction

        Returns:
            204 No Content on success, 404 if not found
        """
        return await action.run(user_id)

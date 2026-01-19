"""User API controller."""

from uuid import UUID

from dishka import FromDishka
from dishka.integrations.litestar import inject
from litestar import Controller as LitestarController
from litestar import delete, get, patch, post
from litestar.params import Parameter

from src.Containers.AppSection.User.Actions import (
    CreateUserAction,
    DeleteUserAction,
    GetUserAction,
    ListUsersAction,
    UpdateUserAction,
)
from src.Containers.AppSection.User.Data.Dto import UserCreateDTO
from src.Containers.AppSection.User.Data.Dto import UserDTO
from src.Containers.AppSection.User.Data.Dto import UserUpdateDTO
class UserController(LitestarController):
    """User API controller."""

    path = "/api/users"

    @post("/")
    @inject
    async def create_user(
        self,
        data: UserCreateDTO,
        action: FromDishka[CreateUserAction],
    ) -> UserDTO:
        """Create a new user.

        Args:
            data: User creation data
            action: Create user action

        Returns:
            Created user
        """
        return await action.run(data)

    @get("/")
    @inject
    async def list_users(
        self,
        action: FromDishka[ListUsersAction],
        limit: int = Parameter(default=100, ge=1, le=1000),
        offset: int = Parameter(default=0, ge=0),
    ) -> list[UserDTO]:
        """List users with pagination.

        Args:
            action: List users action
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of users
        """
        return await action.run({"limit": limit, "offset": offset})

    @get("/{user_id:uuid}")
    @inject
    async def get_user(
        self,
        user_id: UUID,
        action: FromDishka[GetUserAction],
    ) -> UserDTO:
        """Get a user by ID.

        Args:
            user_id: User ID
            action: Get user action

        Returns:
            User details
        """
        return await action.run(user_id)

    @patch("/{user_id:uuid}")
    @inject
    async def update_user(
        self,
        user_id: UUID,
        data: UserUpdateDTO,
        action: FromDishka[UpdateUserAction],
    ) -> UserDTO:
        """Update a user.

        Args:
            user_id: User ID
            data: Update data
            action: Update user action

        Returns:
            Updated user
        """
        return await action.run((user_id, data))

    @delete("/{user_id:uuid}", status_code=204)
    @inject
    async def delete_user(
        self,
        user_id: UUID,
        action: FromDishka[DeleteUserAction],
    ) -> None:
        """Delete a user.

        Args:
            user_id: User ID
            action: Delete user action
        """
        await action.run(user_id)

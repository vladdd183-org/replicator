"""User Server Manager for exposing user functionality."""

from uuid import UUID

from dishka import FromDishka

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
from src.Ship.Parents import ServerManager


class UserServerManager(ServerManager[UserDTO]):
    """Server Manager for User container."""
    
    def __init__(
        self,
        create_action: FromDishka[CreateUserAction],
        get_action: FromDishka[GetUserAction],
        list_action: FromDishka[ListUsersAction],
        update_action: FromDishka[UpdateUserAction],
        delete_action: FromDishka[DeleteUserAction],
    ):
        """Initialize with User actions."""
        self.create_action = create_action
        self.get_action = get_action
        self.list_action = list_action
        self.update_action = update_action
        self.delete_action = delete_action
    
    async def get(self, id: UUID) -> UserDTO | None:
        """Get a user by ID."""
        try:
            return await self.get_action.run(user_id=id)
        except Exception:
            return None
    
    async def list(self, **filters) -> list[UserDTO]:
        """List all users."""
        return await self.list_action.run()
    
    async def create(self, data: UserCreateDTO) -> UserDTO:
        """Create a new user."""
        return await self.create_action.run(data=data)
    
    async def update(self, id: UUID, data: UserUpdateDTO) -> UserDTO | None:
        """Update a user."""
        try:
            return await self.update_action.run(user_id=id, data=data)
        except Exception:
            return None
    
    async def delete(self, id: UUID) -> bool:
        """Delete a user."""
        try:
            await self.delete_action.run(user_id=id)
            return True
        except Exception:
            return False
    
    async def get_by_email(self, email: str) -> UserDTO | None:
        """Get a user by email."""
        # This would need a specific action or task
        # For now, returning None
        return None

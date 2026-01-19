"""Client Manager for accessing User container from Book container."""

from uuid import UUID

from src.Containers.AppSection.User import UserDTO, UserServerManager
from src.Ship.Parents import ClientManager


class UserClientManager(ClientManager[UserDTO]):
    """Client Manager for accessing User functionality from Book container."""
    
    def __init__(self, user_manager: UserServerManager):
        """Initialize with User server manager.
        
        In a real microservices architecture, this would make HTTP calls.
        For now, we're directly using the server manager.
        """
        self.user_manager = user_manager
    
    async def get(self, id: UUID) -> UserDTO | None:
        """Get a user by ID."""
        return await self.user_manager.get(id)
    
    async def list(self, **filters) -> list[UserDTO]:
        """List users."""
        return await self.user_manager.list(**filters)
    
    async def get_by_email(self, email: str) -> UserDTO | None:
        """Get a user by email."""
        return await self.user_manager.get_by_email(email)
    
    async def exists(self, id: UUID) -> bool:
        """Check if a user exists."""
        user = await self.get(id)
        return user is not None

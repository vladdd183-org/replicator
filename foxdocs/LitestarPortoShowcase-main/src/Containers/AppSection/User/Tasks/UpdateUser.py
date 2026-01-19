"""Update user task."""

from datetime import datetime
from uuid import UUID

from src.Containers.AppSection.User.Data.Dto import UserUpdateDTO
from src.Containers.AppSection.User.Data.Repositories import UserRepository
from src.Containers.AppSection.User.Models import User
from src.Ship.Parents import Task


class UpdateUserTask(Task[tuple[UUID, UserUpdateDTO], User | None]):
    """Task for updating a user."""

    def __init__(self, repository: UserRepository) -> None:
        """Initialize task."""
        self.repository = repository

    async def run(self, data: tuple[UUID, UserUpdateDTO]) -> User | None:
        """Update a user."""
        user_id, update_dto = data
        update_data = update_dto.model_dump(exclude_unset=True)
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow()

        return await self.repository.update(user_id, update_data)

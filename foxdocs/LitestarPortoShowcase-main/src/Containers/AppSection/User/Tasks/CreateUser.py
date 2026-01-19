"""Create user task."""

import hashlib
from datetime import datetime
from uuid import uuid4

from src.Containers.AppSection.User.Data.Dto import UserCreateDTO
from src.Containers.AppSection.User.Data.Repositories import UserRepository
from src.Containers.AppSection.User.Models import User
from src.Ship.Parents import Task


class CreateUserTask(Task[UserCreateDTO, User]):
    """Task for creating a user."""

    def __init__(self, repository: UserRepository) -> None:
        """Initialize task."""
        self.repository = repository

    async def run(self, data: UserCreateDTO) -> User:
        """Create a new user."""
        # Hash password (в реальном приложении используйте bcrypt или argon2)
        password_hash = hashlib.sha256(data.password.encode()).hexdigest()
        
        user_data = data.model_dump(exclude={"password"})
        user_data["id"] = uuid4()
        user_data["password_hash"] = password_hash
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()

        return await self.repository.create(user_data)

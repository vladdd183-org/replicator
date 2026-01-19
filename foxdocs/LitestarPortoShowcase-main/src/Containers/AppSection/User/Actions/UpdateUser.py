"""Update user action."""

from uuid import UUID

from src.Containers.AppSection.User.Data.Dto import (
    UserDTO,
    UserUpdateDTO,
)
from src.Containers.AppSection.User.Exceptions import UserNotFoundException
from src.Containers.AppSection.User.UI.API.Transformers import UserTransformer
from src.Containers.AppSection.User.Tasks import UpdateUserTask
from src.Ship.Parents import Action


class UpdateUserAction(Action[tuple[UUID, UserUpdateDTO], UserDTO]):
    """Action for updating a user."""

    def __init__(
        self,
        update_user_task: UpdateUserTask,
        transformer: UserTransformer,
    ) -> None:
        """Initialize action."""
        self.update_user_task = update_user_task
        self.transformer = transformer

    async def run(self, data: tuple[UUID, UserUpdateDTO]) -> UserDTO:
        """Update a user."""
        user = await self.update_user_task.run(data)
        if not user:
            raise UserNotFoundException(user_id=data[0])

        return self.transformer.transform(user)

"""Get user action."""

from uuid import UUID

from src.Containers.AppSection.User.Data.Dto import UserDTO
from src.Containers.AppSection.User.Exceptions import UserNotFoundException
from src.Containers.AppSection.User.UI.API.Transformers import UserTransformer
from src.Containers.AppSection.User.Tasks import FindUserByIdTask
from src.Ship.Parents import Action


class GetUserAction(Action[UUID, UserDTO]):
    """Action for getting a user by ID."""

    def __init__(
        self,
        find_user_task: FindUserByIdTask,
        transformer: UserTransformer,
    ) -> None:
        """Initialize action."""
        self.find_user_task = find_user_task
        self.transformer = transformer

    async def run(self, data: UUID) -> UserDTO:
        """Get a user by ID."""
        user = await self.find_user_task.run(data)
        if not user:
            raise UserNotFoundException(user_id=data)

        return self.transformer.transform(user)

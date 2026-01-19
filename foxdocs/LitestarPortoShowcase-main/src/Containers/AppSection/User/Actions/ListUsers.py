"""List users action."""

from src.Containers.AppSection.User.Data.Dto import UserDTO
from src.Containers.AppSection.User.UI.API.Transformers import UserTransformer
from src.Containers.AppSection.User.Tasks import FindUsersTask
from src.Ship.Parents import Action


class ListUsersAction(Action[dict[str, int], list[UserDTO]]):
    """Action for listing users."""

    def __init__(
        self,
        find_users_task: FindUsersTask,
        transformer: UserTransformer,
    ) -> None:
        """Initialize action."""
        self.find_users_task = find_users_task
        self.transformer = transformer

    async def run(self, data: dict[str, int]) -> list[UserDTO]:
        """List users with pagination."""
        users = await self.find_users_task.run(data)
        return self.transformer.transform_collection(users)

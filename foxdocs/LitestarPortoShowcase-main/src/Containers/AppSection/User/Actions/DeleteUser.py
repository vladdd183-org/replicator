"""Delete user action."""

from uuid import UUID

from src.Containers.AppSection.User.Exceptions import UserNotFoundException
from src.Containers.AppSection.User.Tasks import DeleteUserTask
from src.Ship.Parents import Action


class DeleteUserAction(Action[UUID, None]):
    """Action for deleting a user."""

    def __init__(self, delete_user_task: DeleteUserTask) -> None:
        """Initialize action."""
        self.delete_user_task = delete_user_task

    async def run(self, data: UUID) -> None:
        """Delete a user."""
        deleted = await self.delete_user_task.run(data)
        if not deleted:
            raise UserNotFoundException(user_id=data)

"""Create user action."""

from src.Containers.AppSection.User.Data.Dto import (
    UserCreateDTO,
    UserDTO,
)
from src.Containers.AppSection.User.Exceptions import UserAlreadyExistsException
from src.Containers.AppSection.User.UI.API.Transformers import UserTransformer
from src.Containers.AppSection.User.Tasks import CreateUserTask, FindUserByEmailTask
from src.Ship.Parents import Action


class CreateUserAction(Action[UserCreateDTO, UserDTO]):
    """Action for creating a user."""

    def __init__(
        self,
        find_by_email_task: FindUserByEmailTask,
        create_user_task: CreateUserTask,
        transformer: UserTransformer,
    ) -> None:
        """Initialize action.

        Args:
            find_by_email_task: Task for finding user by email
            create_user_task: Task for creating user
            transformer: User transformer
        """
        self.find_by_email_task = find_by_email_task
        self.create_user_task = create_user_task
        self.transformer = transformer

    async def run(self, data: UserCreateDTO) -> UserDTO:
        """Create a new user.

        Args:
            data: User creation data

        Returns:
            Created user DTO

        Raises:
            UserAlreadyExistsException: If user with email already exists
        """
        # Check if user with email already exists
        existing_user = await self.find_by_email_task.run(data.email)
        if existing_user:
            raise UserAlreadyExistsException(email=data.email)

        # Create the user
        user = await self.create_user_task.run(data)

        # Transform to DTO
        return self.transformer.transform(user)

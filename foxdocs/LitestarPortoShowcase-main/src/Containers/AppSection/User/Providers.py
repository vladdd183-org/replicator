"""User container dependency injection providers."""

from dishka import Provider, Scope, provide

from src.Containers.AppSection.User.Actions import (
    CreateUserAction,
    DeleteUserAction,
    GetUserAction,
    ListUsersAction,
    UpdateUserAction,
)
from src.Containers.AppSection.User.Data.Repositories import UserRepository
from src.Containers.AppSection.User.UI.API.Transformers import UserTransformer
from src.Containers.AppSection.User.Tasks import (
    CreateUserTask,
    DeleteUserTask,
    FindUserByEmailTask,
    FindUserByIdTask,
    FindUsersTask,
    UpdateUserTask,
)


class UserProvider(Provider):
    """User container provider."""

    # Repositories
    @provide(scope=Scope.REQUEST)
    def provide_user_repository(self) -> UserRepository:
        """Provide user repository."""
        return UserRepository()

    # Transformers
    @provide(scope=Scope.APP)
    def provide_user_transformer(self) -> UserTransformer:
        """Provide user transformer."""
        return UserTransformer()

    # Tasks
    @provide(scope=Scope.REQUEST)
    def provide_create_user_task(
        self, repository: UserRepository
    ) -> CreateUserTask:
        """Provide create user task."""
        return CreateUserTask(repository)

    @provide(scope=Scope.REQUEST)
    def provide_find_user_by_id_task(
        self, repository: UserRepository
    ) -> FindUserByIdTask:
        """Provide find user by ID task."""
        return FindUserByIdTask(repository)

    @provide(scope=Scope.REQUEST)
    def provide_find_user_by_email_task(
        self, repository: UserRepository
    ) -> FindUserByEmailTask:
        """Provide find user by email task."""
        return FindUserByEmailTask(repository)

    @provide(scope=Scope.REQUEST)
    def provide_find_users_task(
        self, repository: UserRepository
    ) -> FindUsersTask:
        """Provide find users task."""
        return FindUsersTask(repository)

    @provide(scope=Scope.REQUEST)
    def provide_update_user_task(
        self, repository: UserRepository
    ) -> UpdateUserTask:
        """Provide update user task."""
        return UpdateUserTask(repository)

    @provide(scope=Scope.REQUEST)
    def provide_delete_user_task(
        self, repository: UserRepository
    ) -> DeleteUserTask:
        """Provide delete user task."""
        return DeleteUserTask(repository)

    # Actions
    @provide(scope=Scope.REQUEST)
    def provide_create_user_action(
        self,
        find_by_email_task: FindUserByEmailTask,
        create_task: CreateUserTask,
        transformer: UserTransformer,
    ) -> CreateUserAction:
        """Provide create user action."""
        return CreateUserAction(find_by_email_task, create_task, transformer)

    @provide(scope=Scope.REQUEST)
    def provide_get_user_action(
        self,
        find_task: FindUserByIdTask,
        transformer: UserTransformer,
    ) -> GetUserAction:
        """Provide get user action."""
        return GetUserAction(find_task, transformer)

    @provide(scope=Scope.REQUEST)
    def provide_list_users_action(
        self,
        find_task: FindUsersTask,
        transformer: UserTransformer,
    ) -> ListUsersAction:
        """Provide list users action."""
        return ListUsersAction(find_task, transformer)

    @provide(scope=Scope.REQUEST)
    def provide_update_user_action(
        self,
        update_task: UpdateUserTask,
        transformer: UserTransformer,
    ) -> UpdateUserAction:
        """Provide update user action."""
        return UpdateUserAction(update_task, transformer)

    @provide(scope=Scope.REQUEST)
    def provide_delete_user_action(
        self,
        delete_task: DeleteUserTask,
    ) -> DeleteUserAction:
        """Provide delete user action."""
        return DeleteUserAction(delete_task)

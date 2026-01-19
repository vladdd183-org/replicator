"""User module dependency injection providers.

Consolidated providers with clear scope separation.
Dishka automatically resolves dependencies by type hints.

Architecture:
- UserModuleProvider: APP scope - stateless tasks
- _BaseUserRequestProvider: Base class with common REQUEST scope dependencies  
- UserRequestProvider: HTTP context (inherits base + adds UoW with emit)
- UserCLIProvider: CLI context (inherits base + adds UoW without emit)
"""

from dishka import Provider, Scope, provide
from litestar import Request

from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Actions.DeleteUserAction import DeleteUserAction
from src.Containers.AppSection.UserModule.Actions.UpdateUserAction import UpdateUserAction
from src.Containers.AppSection.UserModule.Actions.AuthenticateAction import AuthenticateAction
from src.Containers.AppSection.UserModule.Actions.ChangePasswordAction import ChangePasswordAction
from src.Containers.AppSection.UserModule.Actions.RefreshTokenAction import RefreshTokenAction
from src.Containers.AppSection.UserModule.Queries.ListUsersQuery import ListUsersQuery
from src.Containers.AppSection.UserModule.Queries.GetUserQuery import GetUserQuery
from src.Containers.AppSection.UserModule.Data.Repositories.UserRepository import UserRepository
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork
from src.Containers.AppSection.UserModule.Tasks.HashPasswordTask import HashPasswordTask
from src.Containers.AppSection.UserModule.Tasks.VerifyPasswordTask import VerifyPasswordTask
from src.Containers.AppSection.UserModule.Tasks.GenerateTokenTask import GenerateTokenTask
from src.Containers.AppSection.UserModule.Tasks.SendWelcomeEmailTask import SendWelcomeEmailTask


class UserModuleProvider(Provider):
    """Core provider for UserModule - APP scope dependencies.
    
    Stateless services that can be reused across requests.
    """
    
    scope = Scope.APP
    
    # Tasks - stateless, reusable
    hash_password_task = provide(HashPasswordTask)
    verify_password_task = provide(VerifyPasswordTask)
    generate_token_task = provide(GenerateTokenTask)
    send_welcome_email_task = provide(SendWelcomeEmailTask)


class _BaseUserRequestProvider(Provider):
    """Base provider with common REQUEST scope dependencies.
    
    Contains all dependencies shared between HTTP and CLI contexts.
    Not exported - use UserRequestProvider or UserCLIProvider instead.
    """
    
    scope = Scope.REQUEST
    
    # Data Layer
    user_repository = provide(UserRepository)
    
    # Queries - CQRS read side
    list_users_query = provide(ListUsersQuery)
    get_user_query = provide(GetUserQuery)
    
    # Actions - CQRS write side
    create_user_action = provide(CreateUserAction)
    update_user_action = provide(UpdateUserAction)
    delete_user_action = provide(DeleteUserAction)
    authenticate_action = provide(AuthenticateAction)
    change_password_action = provide(ChangePasswordAction)
    refresh_token_action = provide(RefreshTokenAction)


class UserRequestProvider(_BaseUserRequestProvider):
    """HTTP request-scoped provider for UserModule.
    
    Extends base provider with UnitOfWork that has event emitter.
    """
    
    @provide
    def provide_user_uow(self, request: Request) -> UserUnitOfWork:
        """Provide UserUnitOfWork with event emitter from request."""
        return UserUnitOfWork(_emit=request.app.emit, _app=request.app)


class UserCLIProvider(_BaseUserRequestProvider):
    """CLI-specific provider for UserModule.
    
    Extends base provider with UnitOfWork without event emitter.
    """
    
    @provide
    def provide_user_uow(self) -> UserUnitOfWork:
        """Provide UserUnitOfWork without event emitter for CLI."""
        return UserUnitOfWork(_emit=None, _app=None)


"""User module actions (Use Cases).

Orchestrate domain logic, use Tasks and Repositories.
Return Result[T, E] for railway-oriented error handling.

Note: GetCurrentUser is now handled via GetUserQuery (CQRS read operation).
"""

from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Actions.UpdateUserAction import (
    UpdateUserAction,
    UpdateUserInput,
)
from src.Containers.AppSection.UserModule.Actions.DeleteUserAction import DeleteUserAction
from src.Containers.AppSection.UserModule.Actions.AuthenticateAction import (
    AuthenticateAction,
    AuthResult,
)
from src.Containers.AppSection.UserModule.Actions.ChangePasswordAction import (
    ChangePasswordAction,
    ChangePasswordInput,
)

__all__ = [
    "CreateUserAction",
    "UpdateUserAction",
    "UpdateUserInput",
    "DeleteUserAction",
    "AuthenticateAction",
    "AuthResult",
    "ChangePasswordAction",
    "ChangePasswordInput",
]

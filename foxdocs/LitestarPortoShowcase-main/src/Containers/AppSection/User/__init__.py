"""User Container - Porto Architecture.

This module provides a clean interface for the User container,
exposing commonly used classes and functions.
"""

# Core Models
from src.Containers.AppSection.User.Models import User

# DTOs
from src.Containers.AppSection.User.Data import UserCreateDTO, UserDTO, UserUpdateDTO, UserRepository

# Actions
from src.Containers.AppSection.User.Actions import (
    CreateUserAction,
    DeleteUserAction,
    GetUserAction,
    ListUsersAction,
    UpdateUserAction,
)

# Tasks
from src.Containers.AppSection.User.Tasks import (
    CreateUserTask,
    DeleteUserTask,
    FindUserByIdTask,
    FindUserByEmailTask,
    FindUsersTask,
    UpdateUserTask,
)

# Exceptions
from src.Containers.AppSection.User.Exceptions import UserAlreadyExistsException, UserNotFoundException

# Transformers are available via .UI.API.Transformers import

# Managers
from src.Containers.AppSection.User.Managers import UserServerManager

__all__ = [
    # Models
    "User",
    # DTOs & Repository
    "UserCreateDTO",
    "UserDTO",
    "UserUpdateDTO", 
    "UserRepository",
    # Actions
    "CreateUserAction",
    "DeleteUserAction",
    "GetUserAction",
    "ListUsersAction",
    "UpdateUserAction",
    # Tasks
    "CreateUserTask",
    "DeleteUserTask",
    "FindUserByIdTask",
    "FindUserByEmailTask",
    "FindUsersTask",
    "UpdateUserTask",
    # Exceptions
    "UserAlreadyExistsException",
    "UserNotFoundException",
    # Transformers available via .UI.API.Transformers import
    # Managers
    "UserServerManager",
]
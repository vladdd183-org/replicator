"""User module errors.

All errors are Pydantic frozen models with explicit http_status.
Uses ErrorWithTemplate for automatic message generation.
"""

from typing import ClassVar
from uuid import UUID

from src.Ship.Core.Errors import BaseError, ErrorWithTemplate


class UserError(BaseError):
    """Base error for UserModule."""

    code: str = "USER_ERROR"


class UserNotFoundError(ErrorWithTemplate, UserError):
    """Error raised when user is not found."""

    _message_template: ClassVar[str] = "User with id {user_id} not found"
    code: str = "USER_NOT_FOUND"
    http_status: int = 404
    user_id: UUID


class UserAlreadyExistsError(ErrorWithTemplate, UserError):
    """Error raised when user with email already exists."""

    _message_template: ClassVar[str] = "User with email {email} already exists"
    code: str = "USER_ALREADY_EXISTS"
    http_status: int = 409
    email: str


class InvalidCredentialsError(UserError):
    """Error raised when credentials are invalid."""

    code: str = "INVALID_CREDENTIALS"
    http_status: int = 401
    message: str = "Invalid email or password"


class UserInactiveError(ErrorWithTemplate, UserError):
    """Error raised when user account is inactive."""

    _message_template: ClassVar[str] = "User account {user_id} is inactive"
    code: str = "USER_INACTIVE"
    http_status: int = 403
    user_id: UUID

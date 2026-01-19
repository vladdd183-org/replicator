"""User-specific exceptions."""

from uuid import UUID

from src.Ship.Parents import PortoException


class UserNotFoundException(PortoException):
    """Exception raised when user is not found."""

    def __init__(self, user_id: UUID | None = None, email: str | None = None) -> None:
        """Initialize exception."""
        if user_id:
            message = f"User with ID {user_id} not found"
            details = {"user_id": str(user_id)}
        else:
            message = f"User with email {email} not found"
            details = {"email": email}

        super().__init__(
            message=message,
            code="USER_NOT_FOUND",
            status_code=404,
            details=details,
        )


class UserAlreadyExistsException(PortoException):
    """Exception raised when user already exists."""

    def __init__(self, email: str) -> None:
        """Initialize exception."""
        super().__init__(
            message=f"User with email {email} already exists",
            code="USER_ALREADY_EXISTS",
            status_code=409,
            details={"email": email},
        )




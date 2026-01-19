"""User module response DTOs.

Response DTOs inherit from EntitySchema for automatic conversion from entities.
"""

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

# Re-export TokenPair from GenerateTokenTask as the single source of truth
from src.Containers.AppSection.UserModule.Tasks.GenerateTokenTask import TokenPair
from src.Ship.Core.BaseSchema import EntitySchema


class UserResponse(EntitySchema):
    """Response DTO for User entity.

    Inherits from_entity() from EntitySchema for automatic conversion.
    Note: password_hash is excluded by not being in the schema.

    Attributes:
        id: User UUID
        email: User's email address
        name: User's display name
        is_active: Whether user account is active
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID
    email: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserListResponse(EntitySchema):
    """Response DTO for list of users.

    Attributes:
        users: List of user responses
        total: Total count of users
        limit: Page size
        offset: Page offset
    """

    users: list[UserResponse]
    total: int
    limit: int
    offset: int


class TokenRefreshResponse(TokenPair):
    """Response DTO for token refresh.

    Inherits directly from TokenPair - no field duplication.
    Adds from_entity for result_handler compatibility.
    """

    @classmethod
    def from_entity(cls, token_pair: TokenPair) -> "TokenRefreshResponse":
        """Create from TokenPair."""
        return cls.model_validate(token_pair, from_attributes=True)


class AuthResponse(EntitySchema):
    """Response DTO for authentication result.

    Flattens TokenPair fields for API compatibility.

    Attributes:
        access_token: JWT access token
        refresh_token: JWT refresh token
        token_type: Token type (Bearer)
        expires_in: Expiration in seconds
        user_id: Authenticated user ID
        email: Authenticated user email
    """

    model_config = ConfigDict(from_attributes=True)

    # Token fields (flattened from TokenPair)
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int

    # User fields
    user_id: str
    email: str

    @classmethod
    def from_entity(cls, auth_result) -> "AuthResponse":
        """Create from AuthResult object.

        This method is called by result_handler decorator.

        Args:
            auth_result: AuthResult from AuthenticateAction

        Returns:
            AuthResponse instance
        """
        return cls(
            access_token=auth_result.tokens.access_token,
            refresh_token=auth_result.tokens.refresh_token,
            token_type=auth_result.tokens.token_type,
            expires_in=auth_result.tokens.expires_in,
            user_id=auth_result.user_id,
            email=auth_result.email,
        )

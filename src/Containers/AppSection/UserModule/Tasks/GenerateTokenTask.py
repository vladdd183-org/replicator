"""Task for generating JWT tokens.

Wraps JWTService for use within Actions.
"""

from uuid import UUID

from pydantic import BaseModel

from src.Ship.Auth.JWT import JWTService
from src.Ship.Parents.Task import SyncTask


class TokenPair(BaseModel):
    """Pair of access and refresh tokens.

    Attributes:
        access_token: JWT access token
        refresh_token: JWT refresh token
        token_type: Token type (always "Bearer")
        expires_in: Access token expiration in seconds
    """

    model_config = {"frozen": True}

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 86400  # 24 hours in seconds


class GenerateTokenInput(BaseModel):
    """Input for token generation.

    Attributes:
        user_id: User UUID
        email: User email
    """

    model_config = {"frozen": True}

    user_id: UUID
    email: str


class GenerateTokenTask(SyncTask[GenerateTokenInput, TokenPair]):
    """Synchronous task for generating JWT token pairs.

    Uses SyncTask because JWTService is CPU-bound and doesn't require I/O.
    Generates both access and refresh tokens for a user.

    Example:
        jwt_service = JWTService()
        task = GenerateTokenTask(jwt_service)
        tokens = task.run(GenerateTokenInput(
            user_id=user.id,
            email=user.email,
        ))
    """

    def __init__(self, jwt_service: JWTService) -> None:
        """Initialize task with JWT service (injected via DI).

        Args:
            jwt_service: JWT service for token generation
        """
        self.jwt_service = jwt_service

    def run(self, data: GenerateTokenInput) -> TokenPair:
        """Generate access and refresh tokens.

        Args:
            data: Token generation input

        Returns:
            TokenPair with access and refresh tokens
        """
        access_token = self.jwt_service.create_access_token(
            user_id=data.user_id,
            email=data.email,
        )

        refresh_token = self.jwt_service.create_refresh_token(
            user_id=data.user_id,
            email=data.email,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.jwt_service.expiration_hours * 3600,
        )

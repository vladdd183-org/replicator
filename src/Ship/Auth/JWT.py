"""JWT Service for token generation and verification.

Uses PyJWT for token operations with configurable expiration and algorithm.
Implements singleton pattern for consistent usage across the application.
"""

from datetime import datetime, timezone, timedelta
from functools import lru_cache
from uuid import UUID
from typing import Any

import jwt
from pydantic import BaseModel

from src.Ship.Configs import get_settings


class TokenPayload(BaseModel):
    """JWT Token payload structure.
    
    Attributes:
        sub: Subject (user ID)
        email: User email
        exp: Expiration timestamp
        iat: Issued at timestamp
        type: Token type (access/refresh)
    """
    
    model_config = {"frozen": True}
    
    sub: UUID
    email: str
    exp: datetime
    iat: datetime
    type: str = "access"


class JWTService:
    """Service for JWT token operations.
    
    Singleton service for token generation, verification, and decoding.
    Use get_jwt_service() to get the cached instance.
    
    Example:
        service = get_jwt_service()
        token = service.create_access_token(user_id, email)
        payload = service.verify_token(token)
    """
    
    def __init__(self) -> None:
        """Initialize JWT service with settings."""
        settings = get_settings()
        self.secret = settings.jwt_secret
        self.algorithm = settings.jwt_algorithm
        self.expiration_hours = settings.jwt_expiration_hours
        self.refresh_expiration_days = settings.jwt_refresh_expiration_days
    
    def create_access_token(
        self,
        user_id: UUID,
        email: str,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        """Create a new access token.
        
        Args:
            user_id: User's UUID
            email: User's email
            extra_claims: Optional additional claims
            
        Returns:
            Encoded JWT token string
        """
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=self.expiration_hours)
        
        payload = {
            "sub": str(user_id),
            "email": email,
            "iat": now,
            "exp": expires,
            "type": "access",
        }
        
        if extra_claims:
            payload.update(extra_claims)
        
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)
    
    def create_refresh_token(
        self,
        user_id: UUID,
        email: str,
    ) -> str:
        """Create a new refresh token.
        
        Refresh tokens have longer expiration (configurable via settings).
        
        Args:
            user_id: User's UUID
            email: User's email
            
        Returns:
            Encoded JWT refresh token string
        """
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=self.refresh_expiration_days)
        
        payload = {
            "sub": str(user_id),
            "email": email,
            "iat": now,
            "exp": expires,
            "type": "refresh",
        }
        
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> TokenPayload | None:
        """Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            TokenPayload if valid, None if invalid/expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
            )
            
            return TokenPayload(
                sub=UUID(payload["sub"]),
                email=payload["email"],
                exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
                iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
                type=payload.get("type", "access"),
            )
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None
    
    def decode_token_unsafe(self, token: str) -> dict[str, Any] | None:
        """Decode token without verification.
        
        Useful for debugging or getting payload from expired tokens.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload dict or None
        """
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False},
            )
        except Exception:
            return None


@lru_cache
def get_jwt_service() -> JWTService:
    """Get cached JWT service instance (singleton).
    
    Returns:
        Cached JWTService instance.
    """
    return JWTService()


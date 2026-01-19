"""User module request DTOs.

Request DTOs use Pydantic for validation.
All Request DTOs are frozen (immutable) for safety.
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CreateUserRequest(BaseModel):
    """Request DTO for creating a new user.
    
    Attributes:
        email: User's email address
        password: User's password (min 8 characters)
        name: User's display name (min 2 characters)
    """
    
    model_config = ConfigDict(frozen=True)
    
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    name: str = Field(..., min_length=2, max_length=100, description="Display name")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UpdateUserRequest(BaseModel):
    """Request DTO for updating a user.
    
    All fields are optional - only provided fields will be updated.
    
    Attributes:
        name: New display name
        is_active: New active status
    """
    
    model_config = ConfigDict(frozen=True)
    
    name: str | None = Field(None, min_length=2, max_length=100)
    is_active: bool | None = None


class ChangePasswordRequest(BaseModel):
    """Request DTO for changing user password.
    
    Attributes:
        current_password: Current password for verification
        new_password: New password to set
    """
    
    model_config = ConfigDict(frozen=True)
    
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    """Request DTO for user login.
    
    Attributes:
        email: User's email address
        password: User's password
    """
    
    model_config = ConfigDict(frozen=True)
    
    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshTokenRequest(BaseModel):
    """Request DTO for token refresh.
    
    Used both for HTTP API and internal Action calls.
    
    Attributes:
        refresh_token: JWT refresh token
    """
    
    model_config = {"frozen": True}
    
    refresh_token: str = Field(..., min_length=1)


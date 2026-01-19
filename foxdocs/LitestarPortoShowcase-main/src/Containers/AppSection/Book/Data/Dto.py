"""Book data transfer objects."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BookCreateDTO(BaseModel):
    """DTO for creating a book."""

    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    isbn: str = Field(..., min_length=13, max_length=13, pattern=r"^\d{13}$")
    description: str = Field(default="")
    is_available: bool = Field(default=True)


class BookUpdateDTO(BaseModel):
    """DTO for updating a book."""

    title: str | None = Field(None, min_length=1, max_length=255)
    author: str | None = Field(None, min_length=1, max_length=255)
    isbn: str | None = Field(None, min_length=13, max_length=13, pattern=r"^\d{13}$")
    description: str | None = None
    is_available: bool | None = None


class BookDTO(BaseModel):
    """DTO for book representation."""

    id: UUID
    title: str
    author: str
    isbn: str
    description: str
    is_available: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

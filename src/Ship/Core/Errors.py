"""Core validation and utility errors."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ValidationError(Exception):
    """Error raised when validation fails."""
    
    message: str
    field_name: Optional[str] = None
    
    def __str__(self) -> str:
        if self.field_name:
            return f"Validation error for '{self.field_name}': {self.message}"
        return f"Validation error: {self.message}"

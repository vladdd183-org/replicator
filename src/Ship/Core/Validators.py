"""Core validation utilities."""

from result import Result, Success, Failure

from src.Ship.Core.Errors import ValidationError


def validate_not_empty(value: str) -> Result[str, ValidationError]:
    """Validate that a string is not empty.
    
    Args:
        value: The string to validate
        
    Returns:
        Success(value) if the string is not empty
        Failure(ValidationError) if the string is empty
    """
    if value:
        return Success(value)
    return Failure(ValidationError(message="Value cannot be empty"))

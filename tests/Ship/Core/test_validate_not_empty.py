"""Tests for validate_not_empty utility."""

import pytest
from result import Success, Failure

from src.Ship.Core import validate_not_empty, ValidationError


class TestValidateNotEmpty:
    """Test cases for validate_not_empty function."""
    
    def test_validate_not_empty_with_non_empty_string(self) -> None:
        """Test that non-empty strings return Success."""
        # Test regular string
        result = validate_not_empty("hello")
        assert isinstance(result, Success)
        assert result.unwrap() == "hello"
        
        # Test string with spaces
        result = validate_not_empty("  hello world  ")
        assert isinstance(result, Success)
        assert result.unwrap() == "  hello world  "
        
        # Test single character
        result = validate_not_empty("a")
        assert isinstance(result, Success)
        assert result.unwrap() == "a"
        
        # Test string with only spaces (still considered non-empty)
        result = validate_not_empty("   ")
        assert isinstance(result, Success)
        assert result.unwrap() == "   "
    
    def test_validate_not_empty_with_empty_string(self) -> None:
        """Test that empty string returns Failure with ValidationError."""
        result = validate_not_empty("")
        assert isinstance(result, Failure)
        
        error = result.failure()
        assert isinstance(error, ValidationError)
        assert error.message == "Value cannot be empty"
        assert error.field_name is None
    
    def test_validate_not_empty_error_string_representation(self) -> None:
        """Test ValidationError string representation."""
        result = validate_not_empty("")
        error = result.failure()
        assert str(error) == "Validation error: Value cannot be empty"
        
        # Test with field_name
        error_with_field = ValidationError(message="Value cannot be empty", field_name="username")
        assert str(error_with_field) == "Validation error for 'username': Value cannot be empty"
    
    def test_validate_not_empty_result_type(self) -> None:
        """Test that function returns proper Result type."""
        # Success case
        success_result = validate_not_empty("test")
        assert success_result.is_ok()
        assert not success_result.is_err()
        
        # Failure case
        failure_result = validate_not_empty("")
        assert failure_result.is_err()
        assert not failure_result.is_ok()

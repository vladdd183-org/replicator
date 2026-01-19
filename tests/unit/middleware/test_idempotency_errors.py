"""Unit tests for idempotency middleware errors.

Tests for all error types in the idempotency middleware.
"""

import pytest

from src.Ship.Middleware.Errors import (
    IdempotencyError,
    IdempotencyKeyRequiredError,
    IdempotencyKeyTooLongError,
    IdempotencyKeyInvalidError,
    IdempotencyConflictError,
    IdempotencyProcessingError,
    IdempotencyCacheError,
)


class TestIdempotencyError:
    """Tests for base IdempotencyError."""
    
    def test_base_error_attributes(self) -> None:
        """Test base error has correct defaults."""
        error = IdempotencyError(message="Test error")
        
        assert error.code == "IDEMPOTENCY_ERROR"
        assert error.http_status == 400
        assert str(error) == "Test error"
    
    def test_error_is_frozen(self) -> None:
        """Test error is immutable."""
        error = IdempotencyError(message="Test error")
        
        with pytest.raises(Exception):  # Pydantic frozen validation error
            error.message = "New message"  # type: ignore


class TestIdempotencyKeyRequiredError:
    """Tests for IdempotencyKeyRequiredError."""
    
    def test_error_attributes(self) -> None:
        """Test error has correct code and status."""
        error = IdempotencyKeyRequiredError(
            method="POST",
            path="/api/v1/payments",
        )
        
        assert error.code == "IDEMPOTENCY_KEY_REQUIRED"
        assert error.http_status == 400
        assert error.method == "POST"
        assert error.path == "/api/v1/payments"
        assert "required" in error.message.lower()


class TestIdempotencyKeyTooLongError:
    """Tests for IdempotencyKeyTooLongError."""
    
    def test_error_with_template(self) -> None:
        """Test error message is generated from template."""
        error = IdempotencyKeyTooLongError(
            max_length=256,
            actual_length=300,
        )
        
        assert error.code == "IDEMPOTENCY_KEY_TOO_LONG"
        assert error.http_status == 400
        assert "256" in error.message
        assert error.max_length == 256
        assert error.actual_length == 300


class TestIdempotencyKeyInvalidError:
    """Tests for IdempotencyKeyInvalidError."""
    
    def test_error_attributes(self) -> None:
        """Test invalid key error."""
        error = IdempotencyKeyInvalidError(key="invalid@key")
        
        assert error.code == "IDEMPOTENCY_KEY_INVALID"
        assert error.http_status == 400
        assert error.key == "invalid@key"
        assert "alphanumeric" in error.message.lower()


class TestIdempotencyConflictError:
    """Tests for IdempotencyConflictError."""
    
    def test_error_returns_409(self) -> None:
        """Test conflict error returns 409."""
        error = IdempotencyConflictError(key="test-key-123")
        
        assert error.code == "IDEMPOTENCY_CONFLICT"
        assert error.http_status == 409
        assert error.key == "test-key-123"
        assert "test-key-123" in error.message
        assert "different request" in error.message.lower()


class TestIdempotencyProcessingError:
    """Tests for IdempotencyProcessingError."""
    
    def test_error_with_retry_after(self) -> None:
        """Test processing error includes retry suggestion."""
        error = IdempotencyProcessingError(
            key="test-key",
            retry_after_seconds=10,
        )
        
        assert error.code == "IDEMPOTENCY_PROCESSING"
        assert error.http_status == 409
        assert error.retry_after_seconds == 10
        assert "10" in error.message
        assert "retry" in error.message.lower()
    
    def test_default_retry_seconds(self) -> None:
        """Test default retry_after_seconds."""
        error = IdempotencyProcessingError(key="test")
        
        assert error.retry_after_seconds == 5


class TestIdempotencyCacheError:
    """Tests for IdempotencyCacheError."""
    
    def test_cache_error_returns_500(self) -> None:
        """Test cache error returns 500."""
        error = IdempotencyCacheError()
        
        assert error.code == "IDEMPOTENCY_CACHE_ERROR"
        assert error.http_status == 500
    
    def test_cache_error_with_original(self) -> None:
        """Test cache error can include original error."""
        error = IdempotencyCacheError(
            original_error="Connection refused",
        )
        
        assert error.original_error == "Connection refused"

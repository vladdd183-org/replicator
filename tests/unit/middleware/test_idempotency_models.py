"""Unit tests for idempotency middleware models.

Tests for IdempotencyRecord, CapturedResponse, and IdempotencyStatus.
"""

import pytest
from datetime import datetime, timedelta, timezone

from pydantic import ValidationError

from src.Ship.Middleware.Models import (
    CapturedResponse,
    IdempotencyRecord,
    IdempotencyStatus,
)


class TestIdempotencyStatus:
    """Tests for IdempotencyStatus enum."""
    
    def test_status_values(self) -> None:
        """Test all status enum values."""
        assert IdempotencyStatus.PROCESSING.value == "processing"
        assert IdempotencyStatus.COMPLETED.value == "completed"
        assert IdempotencyStatus.FAILED.value == "failed"
    
    def test_status_is_string_enum(self) -> None:
        """Test that status can be used as string."""
        assert str(IdempotencyStatus.PROCESSING) == "IdempotencyStatus.PROCESSING"
        assert IdempotencyStatus.COMPLETED == "completed"


class TestCapturedResponse:
    """Tests for CapturedResponse model."""
    
    def test_create_basic_response(self) -> None:
        """Test creating a basic captured response."""
        response = CapturedResponse(
            status_code=200,
            body="SGVsbG8gV29ybGQ=",  # "Hello World" base64
            headers={"x-custom": "value"},
            content_type="text/plain",
        )
        
        assert response.status_code == 200
        assert response.body == "SGVsbG8gV29ybGQ="
        assert response.headers == {"x-custom": "value"}
        assert response.content_type == "text/plain"
    
    def test_response_is_frozen(self) -> None:
        """Test that response is immutable."""
        response = CapturedResponse(
            status_code=200,
            body="dGVzdA==",
        )
        
        with pytest.raises(ValidationError):
            response.status_code = 201  # type: ignore
    
    def test_status_code_validation(self) -> None:
        """Test status code must be valid HTTP code."""
        with pytest.raises(ValidationError):
            CapturedResponse(status_code=99, body="")
        
        with pytest.raises(ValidationError):
            CapturedResponse(status_code=600, body="")
    
    def test_filter_headers(self) -> None:
        """Test header filtering removes hop-by-hop headers."""
        headers = {
            "content-type": "application/json",
            "x-custom": "value",
            "connection": "keep-alive",
            "transfer-encoding": "chunked",
            "content-length": "123",
        }
        
        filtered = CapturedResponse.filter_headers(headers)
        
        assert "content-type" in filtered
        assert "x-custom" in filtered
        assert "connection" not in filtered
        assert "transfer-encoding" not in filtered
        assert "content-length" not in filtered
    
    def test_filter_headers_case_insensitive(self) -> None:
        """Test header filtering is case insensitive."""
        headers = {
            "Connection": "keep-alive",
            "Content-Length": "123",
            "X-Custom": "value",
        }
        
        filtered = CapturedResponse.filter_headers(headers)
        
        assert "Connection" not in filtered
        assert "Content-Length" not in filtered
        assert "X-Custom" in filtered


class TestIdempotencyRecord:
    """Tests for IdempotencyRecord model."""
    
    @pytest.fixture
    def valid_record(self) -> IdempotencyRecord:
        """Create a valid idempotency record."""
        return IdempotencyRecord(
            key="test-key-123",
            status=IdempotencyStatus.PROCESSING,
            request_hash="abc123def456",
            response=None,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            method="POST",
            path="/api/v1/users",
        )
    
    def test_create_processing_record(self, valid_record: IdempotencyRecord) -> None:
        """Test creating a processing record."""
        assert valid_record.key == "test-key-123"
        assert valid_record.status == IdempotencyStatus.PROCESSING
        assert valid_record.response is None
        assert valid_record.is_processing is True
        assert valid_record.is_completed is False
    
    def test_record_is_frozen(self, valid_record: IdempotencyRecord) -> None:
        """Test that record is immutable."""
        with pytest.raises(ValidationError):
            valid_record.key = "new-key"  # type: ignore
    
    def test_key_validation_valid_characters(self) -> None:
        """Test valid key characters (alphanumeric, dash, underscore)."""
        # Valid keys
        valid_keys = [
            "abc123",
            "test-key",
            "test_key",
            "Test-Key_123",
            "a" * 256,  # Max length
        ]
        
        for key in valid_keys:
            record = IdempotencyRecord(
                key=key,
                status=IdempotencyStatus.PROCESSING,
                request_hash="hash",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                method="POST",
                path="/test",
            )
            assert record.key == key
    
    def test_key_validation_invalid_characters(self) -> None:
        """Test invalid key characters raise error."""
        invalid_keys = [
            "test key",  # Space
            "test.key",  # Dot
            "test/key",  # Slash
            "test@key",  # At sign
            "test:key",  # Colon
        ]
        
        for key in invalid_keys:
            with pytest.raises(ValidationError):
                IdempotencyRecord(
                    key=key,
                    status=IdempotencyStatus.PROCESSING,
                    request_hash="hash",
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                    method="POST",
                    path="/test",
                )
    
    def test_key_length_validation(self) -> None:
        """Test key length limits."""
        # Empty key should fail
        with pytest.raises(ValidationError):
            IdempotencyRecord(
                key="",
                status=IdempotencyStatus.PROCESSING,
                request_hash="hash",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                method="POST",
                path="/test",
            )
        
        # Too long key should fail
        with pytest.raises(ValidationError):
            IdempotencyRecord(
                key="a" * 257,
                status=IdempotencyStatus.PROCESSING,
                request_hash="hash",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                method="POST",
                path="/test",
            )
    
    def test_is_expired_property(self) -> None:
        """Test is_expired property."""
        # Not expired
        future_record = IdempotencyRecord(
            key="test",
            status=IdempotencyStatus.COMPLETED,
            request_hash="hash",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            method="POST",
            path="/test",
        )
        assert future_record.is_expired is False
        
        # Expired
        past_record = IdempotencyRecord(
            key="test",
            status=IdempotencyStatus.COMPLETED,
            request_hash="hash",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            method="POST",
            path="/test",
        )
        assert past_record.is_expired is True
    
    def test_with_response_creates_new_record(
        self, valid_record: IdempotencyRecord
    ) -> None:
        """Test with_response returns new immutable record."""
        response = CapturedResponse(
            status_code=201,
            body="eyJpZCI6IjEyMyJ9",
            content_type="application/json",
        )
        
        completed_record = valid_record.with_response(response)
        
        # Original unchanged (frozen)
        assert valid_record.status == IdempotencyStatus.PROCESSING
        assert valid_record.response is None
        
        # New record has response
        assert completed_record.status == IdempotencyStatus.COMPLETED
        assert completed_record.response == response
        assert completed_record.is_completed is True
        
        # Other fields preserved
        assert completed_record.key == valid_record.key
        assert completed_record.request_hash == valid_record.request_hash
        assert completed_record.method == valid_record.method
        assert completed_record.path == valid_record.path
    
    def test_with_response_custom_status(
        self, valid_record: IdempotencyRecord
    ) -> None:
        """Test with_response can set FAILED status."""
        response = CapturedResponse(
            status_code=500,
            body="eyJlcnJvciI6InRlc3QifQ==",
        )
        
        failed_record = valid_record.with_response(
            response, 
            status=IdempotencyStatus.FAILED
        )
        
        assert failed_record.status == IdempotencyStatus.FAILED
    
    def test_json_serialization(self, valid_record: IdempotencyRecord) -> None:
        """Test record can be serialized to JSON."""
        json_str = valid_record.model_dump_json()
        
        # Deserialize back
        restored = IdempotencyRecord.model_validate_json(json_str)
        
        assert restored.key == valid_record.key
        assert restored.status == valid_record.status
        assert restored.request_hash == valid_record.request_hash
        assert restored.method == valid_record.method
        assert restored.path == valid_record.path
    
    def test_json_serialization_with_response(self) -> None:
        """Test record with response serializes correctly."""
        response = CapturedResponse(
            status_code=200,
            body="dGVzdA==",
            headers={"x-custom": "value"},
            content_type="application/json",
        )
        
        record = IdempotencyRecord(
            key="test",
            status=IdempotencyStatus.COMPLETED,
            request_hash="hash",
            response=response,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            method="POST",
            path="/test",
        )
        
        json_str = record.model_dump_json()
        restored = IdempotencyRecord.model_validate_json(json_str)
        
        assert restored.response is not None
        assert restored.response.status_code == 200
        assert restored.response.body == "dGVzdA=="
        assert restored.response.headers == {"x-custom": "value"}

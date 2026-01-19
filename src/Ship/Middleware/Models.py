"""Idempotency middleware data models.

Pydantic models for idempotency record storage and response capture.
All models are immutable (frozen) for thread-safety.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import ClassVar

from pydantic import BaseModel, Field, field_validator


class IdempotencyStatus(str, Enum):
    """Status of an idempotency record.
    
    Attributes:
        PROCESSING: Request is currently being processed
        COMPLETED: Request completed successfully and response is cached
        FAILED: Request failed and error is cached
    """
    
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CapturedResponse(BaseModel):
    """Captured HTTP response data for replay.
    
    Stores all necessary information to reconstruct
    the original response for idempotent replay.
    
    Attributes:
        status_code: HTTP status code (100-599)
        body: Response body as base64-encoded string for binary safety
        headers: Response headers as dict (excluding hop-by-hop headers)
        content_type: Content-Type header value for proper replay
    """
    
    model_config = {"frozen": True}
    
    status_code: int = Field(..., ge=100, le=599, description="HTTP status code")
    body: str = Field(..., description="Base64-encoded response body")
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Response headers (safe to replay)"
    )
    content_type: str | None = Field(
        default=None,
        description="Content-Type header value"
    )
    
    # Headers that should NOT be replayed (hop-by-hop headers)
    SKIP_HEADERS: ClassVar[frozenset[str]] = frozenset({
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "content-length",  # Will be recalculated
        "content-encoding",  # Body is decoded
    })
    
    @classmethod
    def filter_headers(cls, headers: dict[str, str]) -> dict[str, str]:
        """Filter out headers that shouldn't be replayed.
        
        Args:
            headers: Original response headers
            
        Returns:
            Filtered headers safe for replay
        """
        return {
            k: v for k, v in headers.items()
            if k.lower() not in cls.SKIP_HEADERS
        }


class IdempotencyRecord(BaseModel):
    """Idempotency record stored in cache.
    
    Represents a cached request/response pair for idempotent replay.
    The record goes through these states:
    
    1. PROCESSING: Stored when request starts (prevents concurrent duplicates)
    2. COMPLETED: Updated when request completes successfully
    3. FAILED: Updated when request fails (errors are also cached)
    
    Attributes:
        key: Unique idempotency key from X-Idempotency-Key header
        status: Current status of the request
        request_hash: Hash of request body for conflict detection
        response: Captured response (only set when status != PROCESSING)
        created_at: When the record was created
        expires_at: When the record will expire
        method: HTTP method of the original request
        path: URL path of the original request
    """
    
    model_config = {"frozen": True}
    
    key: str = Field(..., min_length=1, max_length=256, description="Idempotency key")
    status: IdempotencyStatus = Field(..., description="Current status")
    request_hash: str = Field(..., description="SHA256 hash of request body")
    response: CapturedResponse | None = Field(
        default=None,
        description="Cached response (null while processing)"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Record creation timestamp"
    )
    expires_at: datetime = Field(..., description="Expiration timestamp")
    method: str = Field(..., description="HTTP method")
    path: str = Field(..., description="Request path")
    
    @field_validator("key")
    @classmethod
    def validate_key_format(cls, v: str) -> str:
        """Validate idempotency key format.
        
        Allows alphanumeric characters, dashes, underscores.
        No spaces or special characters for security.
        """
        import re
        if not re.match(r'^[a-zA-Z0-9_\-]+$', v):
            raise ValueError(
                "Idempotency key must contain only alphanumeric characters, "
                "dashes, and underscores"
            )
        return v
    
    @property
    def is_processing(self) -> bool:
        """Check if request is still being processed."""
        return self.status == IdempotencyStatus.PROCESSING
    
    @property
    def is_completed(self) -> bool:
        """Check if request completed successfully."""
        return self.status == IdempotencyStatus.COMPLETED
    
    @property
    def is_expired(self) -> bool:
        """Check if record has expired."""
        return datetime.now(timezone.utc) > self.expires_at
    
    def with_response(
        self,
        response: CapturedResponse,
        status: IdempotencyStatus = IdempotencyStatus.COMPLETED,
    ) -> "IdempotencyRecord":
        """Create new record with response data.
        
        Since records are frozen, this creates a new instance.
        
        Args:
            response: Captured response to store
            status: New status (COMPLETED or FAILED)
            
        Returns:
            New IdempotencyRecord with response
        """
        return IdempotencyRecord(
            key=self.key,
            status=status,
            request_hash=self.request_hash,
            response=response,
            created_at=self.created_at,
            expires_at=self.expires_at,
            method=self.method,
            path=self.path,
        )

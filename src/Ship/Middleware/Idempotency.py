"""Idempotency Middleware for protecting against duplicate requests.

Implements the idempotency pattern for POST/PUT/PATCH requests using
the X-Idempotency-Key header. Based on Stripe/PayPal patterns.

Flow:
1. Request arrives with X-Idempotency-Key header
2. Check cache for existing record:
   - If PROCESSING: Return 409 (concurrent request)
   - If COMPLETED: Return cached response (idempotent replay)
   - If not found: Create PROCESSING record and continue
3. Execute request, capture response
4. Store response in cache with COMPLETED status
5. Return response

Features:
- Request body hashing for conflict detection
- Configurable TTL (default 24 hours)
- Configurable methods (default: POST, PUT, PATCH)
- Path-based exclusions (e.g., /health, /api/docs)
- Optional enforcement (require key for certain endpoints)
- Graceful degradation on cache failures
- Proper header handling for replay

Usage:
    from src.Ship.Middleware import IdempotencyMiddleware
    
    app = Litestar(
        middleware=[IdempotencyMiddleware],
        ...
    )
    
    # Or with custom config:
    app = Litestar(
        middleware=[
            IdempotencyMiddleware.create_config(
                ttl_seconds=3600,  # 1 hour
                enforce_on_paths=["/api/v1/payments"],
            )
        ],
        ...
    )
"""

import base64
import hashlib
import json
import logfire
import re
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from litestar.middleware import DefineMiddleware, MiddlewareProtocol

from src.Ship.Infrastructure.Cache import cache, ensure_cache_initialized
from src.Ship.Middleware.Errors import (
    IdempotencyConflictError,
    IdempotencyKeyInvalidError,
    IdempotencyKeyRequiredError,
    IdempotencyKeyTooLongError,
    IdempotencyProcessingError,
)
from src.Ship.Middleware.Models import (
    CapturedResponse,
    IdempotencyRecord,
    IdempotencyStatus,
)

if TYPE_CHECKING:
    from litestar.types import ASGIApp, Message, Receive, Scope, Send



class IdempotencyMiddleware(MiddlewareProtocol):
    """Middleware for idempotent request handling.
    
    Prevents duplicate request processing by caching responses
    keyed by the X-Idempotency-Key header value.
    
    Attributes:
        IDEMPOTENT_METHODS: HTTP methods to apply idempotency to
        HEADER_NAME: Header name for idempotency key
        DEFAULT_TTL_SECONDS: Default cache TTL (24 hours)
        MAX_KEY_LENGTH: Maximum allowed key length
        CACHE_KEY_PREFIX: Prefix for cache keys
    
    Configuration Options:
        ttl_seconds: Cache TTL in seconds
        enforce_on_paths: Paths that REQUIRE idempotency key
        exclude_paths: Paths to skip idempotency handling
        include_methods: Override default methods
    """
    
    # Class-level configuration
    IDEMPOTENT_METHODS: frozenset[str] = frozenset({"POST", "PUT", "PATCH"})
    HEADER_NAME: str = "X-Idempotency-Key"
    HEADER_NAME_LOWER: bytes = b"x-idempotency-key"
    DEFAULT_TTL_SECONDS: int = 86400  # 24 hours
    MAX_KEY_LENGTH: int = 256
    CACHE_KEY_PREFIX: str = "idempotency"
    LOCK_TIMEOUT_SECONDS: int = 30  # Processing lock timeout
    
    # Default paths to exclude
    DEFAULT_EXCLUDE_PATHS: frozenset[str] = frozenset({
        "/health",
        "/api/docs",
        "/schema",
        "/static",
        "/graphql",  # GraphQL has its own mutation handling
    })
    
    # Response headers for idempotent responses
    IDEMPOTENCY_REPLAYED_HEADER: str = "X-Idempotency-Replayed"
    RETRY_AFTER_HEADER: str = "Retry-After"
    
    def __init__(
        self,
        app: "ASGIApp",
        ttl_seconds: int | None = None,
        enforce_on_paths: list[str] | None = None,
        exclude_paths: list[str] | None = None,
        include_methods: list[str] | None = None,
    ) -> None:
        """Initialize middleware with configuration.
        
        Args:
            app: ASGI application
            ttl_seconds: Cache TTL in seconds (default: 24 hours)
            enforce_on_paths: Paths that REQUIRE idempotency key
            exclude_paths: Additional paths to exclude
            include_methods: Override default HTTP methods
        """
        self.app = app
        
        self.ttl_seconds = ttl_seconds if ttl_seconds is not None else self.DEFAULT_TTL_SECONDS
        self.enforce_on_paths = frozenset(enforce_on_paths or [])
        self.exclude_paths = self.DEFAULT_EXCLUDE_PATHS | frozenset(exclude_paths or [])
        self.include_methods = frozenset(include_methods) if include_methods else self.IDEMPOTENT_METHODS
        
        # Ensure cache is initialized
        ensure_cache_initialized()
    
    @classmethod
    def create_config(
        cls,
        ttl_seconds: int | None = None,
        enforce_on_paths: list[str] | None = None,
        exclude_paths: list[str] | None = None,
        include_methods: list[str] | None = None,
    ) -> DefineMiddleware:
        """Create middleware configuration for custom settings.
        
        Usage:
            app = Litestar(
                middleware=[
                    IdempotencyMiddleware.create_config(
                        ttl_seconds=3600,
                        enforce_on_paths=["/api/v1/payments"],
                    )
                ],
            )
        
        Args:
            ttl_seconds: Cache TTL in seconds
            enforce_on_paths: Paths requiring idempotency key
            exclude_paths: Paths to skip
            include_methods: HTTP methods to handle
            
        Returns:
            DefineMiddleware instance for Litestar
        """
        return DefineMiddleware(
            cls,
            ttl_seconds=ttl_seconds,
            enforce_on_paths=enforce_on_paths,
            exclude_paths=exclude_paths,
            include_methods=include_methods,
        )
    
    async def __call__(
        self,
        scope: "Scope",
        receive: "Receive",
        send: "Send",
    ) -> None:
        """Process request with idempotency handling.
        
        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        # Skip non-HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        method = scope.get("method", "")
        path = scope.get("path", "")
        
        # Skip excluded paths
        if self._should_skip_path(path):
            await self.app(scope, receive, send)
            return
        
        # Skip methods not configured for idempotency
        if method not in self.include_methods:
            await self.app(scope, receive, send)
            return
        
        # Extract idempotency key from headers
        headers = dict(scope.get("headers", []))
        idempotency_key = self._extract_idempotency_key(headers)
        
        # Check if key is required for this path
        if not idempotency_key:
            if self._requires_key(path):
                await self._send_error_response(
                    send,
                    IdempotencyKeyRequiredError(method=method, path=path),
                )
                return
            # Key not required and not provided - process normally
            await self.app(scope, receive, send)
            return
        
        # Validate key format
        validation_error = self._validate_key(idempotency_key)
        if validation_error:
            await self._send_error_response(send, validation_error)
            return
        
        # Read request body for hashing
        body = await self._read_body(receive)
        request_hash = self._hash_request(method, path, body)
        
        # Generate cache key
        cache_key = self._make_cache_key(idempotency_key)
        
        # Check for existing record
        try:
            existing_record = await self._get_record(cache_key)
        except Exception as e:
            logfire.warn(
                f"Idempotency cache read failed, processing normally: {e}"
            )
            # Graceful degradation - process without idempotency
            await self._process_with_body(scope, body, send)
            return
        
        if existing_record:
            # Check if request hash matches (detect conflicts)
            if existing_record.request_hash != request_hash:
                await self._send_error_response(
                    send,
                    IdempotencyConflictError(key=idempotency_key),
                )
                return
            
            # Check status
            if existing_record.is_processing:
                # Concurrent request - return 409 with Retry-After
                await self._send_error_response(
                    send,
                    IdempotencyProcessingError(
                        key=idempotency_key,
                        retry_after_seconds=5,
                    ),
                    retry_after=5,
                )
                return
            
            if existing_record.response:
                # Return cached response
                await self._send_cached_response(
                    send,
                    existing_record.response,
                    idempotency_key,
                )
                return
        
        # Create processing record
        try:
            record = IdempotencyRecord(
                key=idempotency_key,
                status=IdempotencyStatus.PROCESSING,
                request_hash=request_hash,
                response=None,
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=self.ttl_seconds),
                method=method,
                path=path,
            )
            await self._set_record(cache_key, record, ttl=self.LOCK_TIMEOUT_SECONDS)
        except Exception as e:
            logfire.warn(f"Idempotency cache write failed: {e}")
            # Continue processing without idempotency
            await self._process_with_body(scope, body, send)
            return
        
        # Execute request and capture response
        captured_response = await self._capture_and_send_response(
            scope, body, send
        )
        
        # Update record with response
        try:
            completed_record = record.with_response(
                captured_response,
                IdempotencyStatus.COMPLETED,
            )
            await self._set_record(cache_key, completed_record, ttl=self.ttl_seconds)
        except Exception as e:
            logfire.warn(f"Idempotency cache update failed: {e}")
            # Response already sent, just log the error
    
    def _should_skip_path(self, path: str) -> bool:
        """Check if path should be skipped.
        
        Args:
            path: Request path
            
        Returns:
            True if path should skip idempotency handling
        """
        return any(path.startswith(exc) for exc in self.exclude_paths)
    
    def _requires_key(self, path: str) -> bool:
        """Check if path requires idempotency key.
        
        Args:
            path: Request path
            
        Returns:
            True if idempotency key is required
        """
        return any(path.startswith(p) for p in self.enforce_on_paths)
    
    def _extract_idempotency_key(self, headers: dict[bytes, bytes]) -> str | None:
        """Extract idempotency key from headers.
        
        Args:
            headers: Request headers as bytes dict
            
        Returns:
            Idempotency key string or None
        """
        key_bytes = headers.get(self.HEADER_NAME_LOWER)
        if key_bytes:
            return key_bytes.decode("utf-8", errors="ignore").strip()
        return None
    
    def _validate_key(self, key: str) -> Any | None:
        """Validate idempotency key format.
        
        Args:
            key: Idempotency key to validate
            
        Returns:
            Error if validation fails, None if valid
        """
        if len(key) > self.MAX_KEY_LENGTH:
            return IdempotencyKeyTooLongError(
                max_length=self.MAX_KEY_LENGTH,
                actual_length=len(key),
            )
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9_\-]+$', key):
            return IdempotencyKeyInvalidError(key=key[:50])  # Truncate for safety
        
        return None
    
    async def _read_body(self, receive: "Receive") -> bytes:
        """Read complete request body.
        
        Args:
            receive: ASGI receive callable
            
        Returns:
            Complete request body as bytes
        """
        body_parts: list[bytes] = []
        
        while True:
            message = await receive()
            body = message.get("body", b"")
            if body:
                body_parts.append(body)
            if not message.get("more_body", False):
                break
        
        return b"".join(body_parts)
    
    def _hash_request(self, method: str, path: str, body: bytes) -> str:
        """Create hash of request for conflict detection.
        
        Args:
            method: HTTP method
            path: Request path
            body: Request body
            
        Returns:
            SHA256 hash of request
        """
        content = f"{method}:{path}:".encode() + body
        return hashlib.sha256(content).hexdigest()
    
    def _make_cache_key(self, idempotency_key: str) -> str:
        """Generate cache key from idempotency key.
        
        Args:
            idempotency_key: Client-provided idempotency key
            
        Returns:
            Full cache key with prefix
        """
        return f"{self.CACHE_KEY_PREFIX}:{idempotency_key}"
    
    async def _get_record(self, cache_key: str) -> IdempotencyRecord | None:
        """Get idempotency record from cache.
        
        Args:
            cache_key: Cache key
            
        Returns:
            IdempotencyRecord or None if not found
        """
        data = await cache.get(cache_key)
        if data:
            return IdempotencyRecord.model_validate_json(data)
        return None
    
    async def _set_record(
        self,
        cache_key: str,
        record: IdempotencyRecord,
        ttl: int,
    ) -> None:
        """Store idempotency record in cache.
        
        Args:
            cache_key: Cache key
            record: Record to store
            ttl: TTL in seconds
        """
        await cache.set(
            cache_key,
            record.model_dump_json(),
            expire=ttl,  # cashews uses 'expire' not 'ttl'
        )
    
    async def _process_with_body(
        self,
        scope: "Scope",
        body: bytes,
        send: "Send",
    ) -> None:
        """Process request with pre-read body.
        
        Creates a new receive function that returns the pre-read body.
        
        Args:
            scope: ASGI scope
            body: Pre-read body
            send: ASGI send callable
        """
        body_sent = False
        
        async def receive() -> "Message":
            nonlocal body_sent
            if not body_sent:
                body_sent = True
                return {
                    "type": "http.request",
                    "body": body,
                    "more_body": False,
                }
            return {
                "type": "http.request",
                "body": b"",
                "more_body": False,
            }
        
        await self.app(scope, receive, send)
    
    async def _capture_and_send_response(
        self,
        scope: "Scope",
        body: bytes,
        send: "Send",
    ) -> CapturedResponse:
        """Execute request, capture response, and send to client.
        
        Args:
            scope: ASGI scope
            body: Request body
            send: ASGI send callable
            
        Returns:
            Captured response data
        """
        response_started = False
        status_code = 500
        response_headers: dict[str, str] = {}
        response_body_parts: list[bytes] = []
        content_type: str | None = None
        
        async def capture_send(message: "Message") -> None:
            nonlocal response_started, status_code, response_headers, content_type
            
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message.get("status", 500)
                
                # Capture headers
                raw_headers = message.get("headers", [])
                for name, value in raw_headers:
                    name_str = name.decode("utf-8") if isinstance(name, bytes) else name
                    value_str = value.decode("utf-8") if isinstance(value, bytes) else value
                    response_headers[name_str] = value_str
                    if name_str.lower() == "content-type":
                        content_type = value_str
                
                await send(message)
                
            elif message["type"] == "http.response.body":
                body_chunk = message.get("body", b"")
                if body_chunk:
                    response_body_parts.append(body_chunk)
                await send(message)
        
        body_sent = False
        
        async def receive() -> "Message":
            nonlocal body_sent
            if not body_sent:
                body_sent = True
                return {
                    "type": "http.request",
                    "body": body,
                    "more_body": False,
                }
            return {
                "type": "http.request",
                "body": b"",
                "more_body": False,
            }
        
        await self.app(scope, receive, capture_send)
        
        # Create captured response
        full_body = b"".join(response_body_parts)
        filtered_headers = CapturedResponse.filter_headers(response_headers)
        
        return CapturedResponse(
            status_code=status_code,
            body=base64.b64encode(full_body).decode("utf-8"),
            headers=filtered_headers,
            content_type=content_type,
        )
    
    async def _send_cached_response(
        self,
        send: "Send",
        response: CapturedResponse,
        idempotency_key: str,
    ) -> None:
        """Send cached response to client.
        
        Adds X-Idempotency-Replayed header to indicate replay.
        
        Args:
            send: ASGI send callable
            response: Cached response data
            idempotency_key: Key used for lookup
        """
        # Decode body
        body = base64.b64decode(response.body)
        
        # Build headers
        headers: list[tuple[bytes, bytes]] = [
            (self.IDEMPOTENCY_REPLAYED_HEADER.encode(), b"true"),
            (b"content-length", str(len(body)).encode()),
        ]
        
        # Add cached headers
        for name, value in response.headers.items():
            headers.append((name.encode(), value.encode()))
        
        # Add content-type if available
        if response.content_type:
            headers.append((b"content-type", response.content_type.encode()))
        
        # Send response
        await send({
            "type": "http.response.start",
            "status": response.status_code,
            "headers": headers,
        })
        
        await send({
            "type": "http.response.body",
            "body": body,
            "more_body": False,
        })
        
        logfire.debug(f"Replayed cached response for idempotency key: {idempotency_key}")
    
    async def _send_error_response(
        self,
        send: "Send",
        error: Any,
        retry_after: int | None = None,
    ) -> None:
        """Send error response to client.
        
        Formats error as RFC 9457 Problem Details JSON.
        
        Args:
            send: ASGI send callable
            error: Error instance with http_status, code, message
            retry_after: Optional Retry-After header value
        """
        # Build Problem Details response
        problem = {
            "type": f"urn:error:{error.code.lower()}",
            "title": error.code.replace("_", " ").title(),
            "status": error.http_status,
            "detail": error.message,
        }
        
        body = json.dumps(problem).encode("utf-8")
        
        headers: list[tuple[bytes, bytes]] = [
            (b"content-type", b"application/problem+json"),
            (b"content-length", str(len(body)).encode()),
        ]
        
        if retry_after is not None:
            headers.append((self.RETRY_AFTER_HEADER.encode(), str(retry_after).encode()))
        
        await send({
            "type": "http.response.start",
            "status": error.http_status,
            "headers": headers,
        })
        
        await send({
            "type": "http.response.body",
            "body": body,
            "more_body": False,
        })

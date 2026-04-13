"""Gateway-specific error classes.

These errors are used by gateway adapters to represent
transport-level failures in a domain-agnostic way.

Error Hierarchy:
    GatewayError (base)
    ├── GatewayConnectionError - Cannot connect to service
    ├── GatewayTimeoutError - Request timed out
    ├── GatewayUnavailableError - Service is unavailable
    ├── GatewayResponseError - Invalid/unexpected response
    ├── GatewayAuthenticationError - Auth failed
    └── GatewayCircuitOpenError - Circuit breaker is open

Usage:
    Gateway adapters catch transport errors and wrap them
    in appropriate GatewayError subclasses for consistent handling.

    Consumer modules can then map these to their domain errors
    or handle them generically.

Example:
    try:
        response = await self.client.post(url, json=data)
    except httpx.ConnectError as e:
        return Failure(GatewayConnectionError(
            service_name="payment-service",
            details=str(e),
        ))
    except httpx.TimeoutException as e:
        return Failure(GatewayTimeoutError(
            service_name="payment-service",
            timeout_seconds=30.0,
        ))
"""

from typing import Any, ClassVar

from src.Ship.Core.Errors import BaseError, ErrorWithTemplate


class GatewayError(BaseError):
    """Base error for all gateway-related failures.

    All gateway errors inherit from this class.
    Allows catching all gateway errors with single except clause.

    Attributes:
        service_name: Name of the target service/module
        code: Machine-readable error code
    """

    code: str = "GATEWAY_ERROR"
    http_status: int = 502  # Bad Gateway
    service_name: str


class GatewayConnectionError(ErrorWithTemplate, GatewayError):
    """Error raised when gateway cannot connect to target service.

    Causes:
    - Service is down
    - Network issues
    - DNS resolution failed
    - Connection refused

    Retry Strategy: Exponential backoff with jitter
    """

    _message_template: ClassVar[str] = "Cannot connect to service '{service_name}': {details}"
    code: str = "GATEWAY_CONNECTION_ERROR"
    http_status: int = 503  # Service Unavailable
    details: str = "Connection failed"


class GatewayTimeoutError(ErrorWithTemplate, GatewayError):
    """Error raised when gateway request times out.

    Causes:
    - Service is overloaded
    - Network latency
    - Long-running operation

    Retry Strategy: Limited retries with increased timeout
    """

    _message_template: ClassVar[str] = (
        "Request to service '{service_name}' timed out after {timeout_seconds}s"
    )
    code: str = "GATEWAY_TIMEOUT"
    http_status: int = 504  # Gateway Timeout
    timeout_seconds: float


class GatewayUnavailableError(ErrorWithTemplate, GatewayError):
    """Error raised when target service is temporarily unavailable.

    Causes:
    - Service is starting up
    - Service is in maintenance mode
    - Service returned 503

    Retry Strategy: Wait and retry with backoff
    """

    _message_template: ClassVar[str] = (
        "Service '{service_name}' is temporarily unavailable: {reason}"
    )
    code: str = "GATEWAY_UNAVAILABLE"
    http_status: int = 503  # Service Unavailable
    reason: str = "Service unavailable"


class GatewayResponseError(ErrorWithTemplate, GatewayError):
    """Error raised when gateway receives invalid/unexpected response.

    Causes:
    - Invalid JSON in response
    - Unexpected response format
    - Schema mismatch
    - Deserialization failed

    Retry Strategy: Do not retry (likely a bug)
    """

    _message_template: ClassVar[str] = "Invalid response from service '{service_name}': {details}"
    code: str = "GATEWAY_RESPONSE_ERROR"
    http_status: int = 502  # Bad Gateway
    details: str
    raw_response: str | None = None


class GatewayAuthenticationError(ErrorWithTemplate, GatewayError):
    """Error raised when gateway authentication fails.

    Causes:
    - Invalid API key
    - Expired token
    - Missing credentials
    - Service-to-service auth failed

    Retry Strategy: Do not retry without new credentials
    """

    _message_template: ClassVar[str] = (
        "Authentication failed for service '{service_name}': {reason}"
    )
    code: str = "GATEWAY_AUTH_ERROR"
    http_status: int = 401  # Unauthorized
    reason: str = "Authentication failed"


class GatewayCircuitOpenError(ErrorWithTemplate, GatewayError):
    """Error raised when circuit breaker is open.

    Circuit breaker is open when too many recent failures occurred.
    Prevents cascade failures by failing fast.

    Retry Strategy: Wait for circuit to close (half-open state)

    Attributes:
        open_since: Timestamp when circuit opened
        retry_after_seconds: Suggested retry delay
    """

    _message_template: ClassVar[str] = (
        "Circuit breaker is open for service '{service_name}'. Retry after {retry_after_seconds}s."
    )
    code: str = "GATEWAY_CIRCUIT_OPEN"
    http_status: int = 503  # Service Unavailable
    retry_after_seconds: float = 30.0
    failure_count: int = 0


class GatewayRateLimitError(ErrorWithTemplate, GatewayError):
    """Error raised when rate limit is exceeded.

    Causes:
    - Too many requests to target service
    - Service returned 429

    Retry Strategy: Wait for rate limit window to reset
    """

    _message_template: ClassVar[str] = (
        "Rate limit exceeded for service '{service_name}'. Retry after {retry_after_seconds}s."
    )
    code: str = "GATEWAY_RATE_LIMIT"
    http_status: int = 429  # Too Many Requests
    retry_after_seconds: float = 60.0


class GatewayServerError(ErrorWithTemplate, GatewayError):
    """Error raised when target service returns 5xx error.

    Causes:
    - Internal server error in target service
    - Database issues
    - Unhandled exception

    Retry Strategy: Limited retries with exponential backoff
    """

    _message_template: ClassVar[str] = (
        "Service '{service_name}' returned error {status_code}: {details}"
    )
    code: str = "GATEWAY_SERVER_ERROR"
    http_status: int = 502  # Bad Gateway
    status_code: int = 500
    details: str = "Internal server error"


class GatewayClientError(ErrorWithTemplate, GatewayError):
    """Error raised when target service returns 4xx error (except 401, 429).

    Causes:
    - Bad request (400)
    - Not found (404)
    - Conflict (409)
    - Validation error (422)

    Retry Strategy: Do not retry (request is invalid)
    """

    _message_template: ClassVar[str] = (
        "Service '{service_name}' rejected request with {status_code}: {details}"
    )
    code: str = "GATEWAY_CLIENT_ERROR"
    http_status: int = 400  # Bad Request (will be overridden based on status_code)
    status_code: int = 400
    details: str = "Bad request"
    validation_errors: dict[str, Any] | None = None


__all__ = [
    "GatewayError",
    "GatewayConnectionError",
    "GatewayTimeoutError",
    "GatewayUnavailableError",
    "GatewayResponseError",
    "GatewayAuthenticationError",
    "GatewayCircuitOpenError",
    "GatewayRateLimitError",
    "GatewayServerError",
    "GatewayClientError",
]

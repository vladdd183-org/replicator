"""Rate limiting middleware using Litestar's built-in rate limiter.

Provides protection against abuse by limiting request rates.
Based on IETF RateLimit draft specification.

Features:
- IP-based rate limiting
- Configurable time windows (second, minute, hour, day)
- Path exclusions
- Custom throttle handlers (user-based, API key-based)
- IETF-compliant RateLimit-* headers

Headers returned:
- RateLimit-Limit: Maximum requests allowed
- RateLimit-Remaining: Remaining requests in window
- RateLimit-Reset: Seconds until limit resets

Example usage in App.py:
    from src.Ship.Infrastructure.RateLimiting import create_rate_limit_config
    
    app = Litestar(
        middleware=[create_rate_limit_config().middleware],
        ...
    )

Example usage on specific route:
    from src.Ship.Infrastructure.RateLimiting import strict_rate_limit
    
    @get("/api/expensive", middleware=[strict_rate_limit.middleware])
    async def expensive_endpoint() -> dict:
        ...
"""

from typing import TYPE_CHECKING

from litestar.middleware.rate_limit import RateLimitConfig

from src.Ship.Auth.Middleware import get_auth_user_from_request

if TYPE_CHECKING:
    from litestar.connection import Request


def get_client_ip(request: "Request") -> str:
    """Extract client IP for rate limiting.
    
    Handles X-Forwarded-For header for proxied requests.
    Priority: X-Forwarded-For > X-Real-IP > Direct connection
    
    Args:
        request: Litestar request
        
    Returns:
        Client IP address
    """
    # Check X-Forwarded-For header (from reverse proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP (client IP)
        return forwarded_for.split(",")[0].strip()
    
    # Check X-Real-IP header (nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    client = request.client
    if client:
        return client.host
    
    return "unknown"


def get_user_id(request: "Request") -> str:
    """Extract user ID for per-user rate limiting.
    
    Uses authenticated user if available, otherwise falls back to IP.
    
    Args:
        request: Litestar request
        
    Returns:
        User identifier (user_id or IP)
    """
    # Preferred: our AuthenticationMiddleware stores auth context in request.state.auth_user
    auth_user = get_auth_user_from_request(request)
    if auth_user is not None:
        return f"user:{auth_user.id}"

    # Backward/compatibility: some integrations may store a user object in request.scope["user"]
    scope_user = request.scope.get("user")
    if scope_user is not None and hasattr(scope_user, "id"):
        return f"user:{scope_user.id}"
    
    # Fallback to IP-based throttling
    return f"ip:{get_client_ip(request)}"


def get_api_key(request: "Request") -> str:
    """Extract API key for API key-based rate limiting.
    
    Checks Authorization header and X-API-Key header.
    
    Args:
        request: Litestar request
        
    Returns:
        API key identifier or IP fallback
    """
    # Check X-API-Key header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api:{api_key[:16]}"  # Use prefix for privacy
    
    # Check Bearer token
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        return f"token:{token[:16]}"  # Use prefix
    
    # Fallback to IP
    return f"ip:{get_client_ip(request)}"


# =============================================================================
# Pre-configured Rate Limit Configurations
# =============================================================================

# Default: 100 requests per minute per IP
# Good for general API endpoints
default_rate_limit = RateLimitConfig(
    rate_limit=("minute", 100),
    exclude=[
        "/health",
        "/health/ready",
        "/health/live",
        "/api/docs",
        "/api/docs/openapi.json",
    ],
    check_throttle_handler=get_client_ip,
)

# Strict: 10 requests per minute per IP
# Good for: login, password reset, registration
auth_rate_limit = RateLimitConfig(
    rate_limit=("minute", 10),
    check_throttle_handler=get_client_ip,
)

# Relaxed: 1000 requests per minute per IP
# Good for: high-frequency endpoints like search autocomplete
relaxed_rate_limit = RateLimitConfig(
    rate_limit=("minute", 1000),
    check_throttle_handler=get_client_ip,
)

# Per-second: 5 requests per second per IP
# Good for: preventing burst requests
burst_rate_limit = RateLimitConfig(
    rate_limit=("second", 5),
    check_throttle_handler=get_client_ip,
)

# Per-user: 200 requests per minute per authenticated user
# Good for: authenticated API with different limits than anonymous
user_rate_limit = RateLimitConfig(
    rate_limit=("minute", 200),
    check_throttle_handler=get_user_id,
)

# API key-based: 500 requests per minute per API key
# Good for: external API integrations
api_key_rate_limit = RateLimitConfig(
    rate_limit=("minute", 500),
    check_throttle_handler=get_api_key,
)

# Very strict: 3 requests per minute per IP
# Good for: expensive operations like exports, reports
strict_rate_limit = RateLimitConfig(
    rate_limit=("minute", 3),
    check_throttle_handler=get_client_ip,
)


# =============================================================================
# Factory Functions
# =============================================================================

def create_rate_limit_config(
    rate_limit: tuple[str, int] = ("minute", 100),
    exclude: list[str] | None = None,
    use_user_id: bool = False,
    use_api_key: bool = False,
) -> RateLimitConfig:
    """Create custom rate limit configuration.
    
    Args:
        rate_limit: Tuple of (time_unit, count). Time unit can be:
                   'second', 'minute', 'hour', 'day'
        exclude: List of paths to exclude from rate limiting
        use_user_id: Use authenticated user ID instead of IP
        use_api_key: Use API key instead of IP
        
    Returns:
        RateLimitConfig for use in Litestar app or route
        
    Example:
        # 50 requests per hour for expensive endpoint
        config = create_rate_limit_config(
            rate_limit=("hour", 50),
            exclude=["/health"],
        )
        
        @get("/api/reports", middleware=[config.middleware])
        async def get_report() -> dict:
            ...
    """
    # Determine throttle handler
    if use_user_id:
        throttle_handler = get_user_id
    elif use_api_key:
        throttle_handler = get_api_key
    else:
        throttle_handler = get_client_ip
    
    return RateLimitConfig(
        rate_limit=rate_limit,
        exclude=exclude or [],
        check_throttle_handler=throttle_handler,
    )


def create_global_rate_limit() -> RateLimitConfig:
    """Create default global rate limit middleware.
    
    Returns:
        RateLimitConfig configured for global use in Litestar app
        
    Example:
        app = Litestar(
            middleware=[create_global_rate_limit().middleware],
            ...
        )
    """
    return default_rate_limit


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Throttle handlers
    "get_client_ip",
    "get_user_id",
    "get_api_key",
    # Pre-configured limits
    "default_rate_limit",
    "auth_rate_limit",
    "relaxed_rate_limit",
    "burst_rate_limit",
    "user_rate_limit",
    "api_key_rate_limit",
    "strict_rate_limit",
    # Factory functions
    "create_rate_limit_config",
    "create_global_rate_limit",
]


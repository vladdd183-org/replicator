"""Cashews cache configuration.

Provides a configured cache instance with lazy initialization.
Uses in-memory cache for development and Redis for production.

Usage:
    from cashews import cache
    from datetime import timedelta
    
    # Caching decorator
    @cache(ttl=timedelta(minutes=5), key="user:{user_id}")
    async def get_user(user_id: str) -> User:
        ...
    
    # Manual invalidation (use invalidate_cache from cache_utils.py)
    from src.Ship.Decorators.cache_utils import invalidate_cache
    await invalidate_cache("user:123", "users:list:*")
"""

from cashews import cache

# Track initialization state
_cache_initialized = False


def setup_cache() -> None:
    """Setup cache backend based on environment.
    
    This function is idempotent - can be called multiple times safely.
    Uses lazy initialization to avoid issues with testing and CLI.
    """
    global _cache_initialized
    
    if _cache_initialized:
        return
    
    from src.Ship.Configs import get_settings
    settings = get_settings()
    
    if settings.is_production:
        cache.setup(settings.redis_url)
    else:
        cache.setup("mem://")
    
    _cache_initialized = True


def ensure_cache_initialized() -> None:
    """Ensure cache is initialized before use.
    
    Call this at the start of any entry point that needs caching.
    """
    if not _cache_initialized:
        setup_cache()


def reset_cache_for_testing() -> None:
    """Reset cache initialization state for testing.
    
    Use in test fixtures to allow reconfiguration.
    """
    global _cache_initialized
    _cache_initialized = False


"""Cache utility functions.

Single source of truth for cache invalidation.

For caching reads, use cashews @cache decorator directly:
    from src.Ship.Infrastructure.Cache import cache
    
    @cache(ttl=timedelta(minutes=5), key="user:{user_id}")
    async def get_user(user_id: UUID) -> User:
        ...

For invalidation, use invalidate_cache() function:
    await invalidate_cache("user:123", "users:list:*")
"""

from src.Ship.Infrastructure.Cache import cache
from src.Ship.Infrastructure.Cache.Cashews import ensure_cache_initialized


async def invalidate_cache(*patterns: str) -> None:
    """Invalidate cache entries matching patterns.
    
    This is the ONLY cache invalidation function you should use.
    Supports wildcards via cashews delete_match.
    Ensures cache is initialized before use.
    
    Args:
        patterns: Cache key patterns to delete (supports * wildcards)
        
    Example:
        # Single key
        await invalidate_cache("user:123")
        
        # Multiple patterns
        await invalidate_cache("user:123", "users:list:*", "users:count")
        
        # Wildcard all user caches
        await invalidate_cache("user:*", "users:*")
    """
    ensure_cache_initialized()
    
    for pattern in patterns:
        if "*" in pattern:
            await cache.delete_match(pattern)
        else:
            await cache.delete(pattern)


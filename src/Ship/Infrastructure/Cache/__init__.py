"""Cache infrastructure module.

Exports cache configuration and utilities.
For invalidation use: from src.Ship.Decorators.cache_utils import invalidate_cache

Cache is lazily initialized on first use. Call setup_cache() explicitly
in application startup if you need eager initialization.
"""

from cashews import cache

from src.Ship.Infrastructure.Cache.Cashews import (
    setup_cache,
    ensure_cache_initialized,
    reset_cache_for_testing,
)

__all__ = [
    "cache",
    "setup_cache",
    "ensure_cache_initialized",
    "reset_cache_for_testing",
]

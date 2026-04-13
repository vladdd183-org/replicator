"""Rate limiting decorator for async functions."""

import asyncio
import functools
import time
from typing import Any, Callable, TypeVar, cast

F = TypeVar('F', bound=Callable[..., Any])


def rate_limit(max_calls: int, period_seconds: float) -> Callable[[F], F]:
    """Decorator to limit the rate of async function calls.
    
    Args:
        max_calls: Maximum number of calls allowed within the period
        period_seconds: Time window in seconds for the rate limit
        
    Returns:
        Decorated function that enforces rate limiting
        
    Example:
        @rate_limit(max_calls=10, period_seconds=60.0)
        async def api_call():
            return await fetch_data()
    """
    def decorator(func: F) -> F:
        # Validate that the function is async
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f"rate_limit can only be applied to async functions, got {func}")
            
        # Create a semaphore to limit concurrent calls
        semaphore = asyncio.Semaphore(max_calls)
        # Track the start time of the current period
        period_start = time.monotonic()
        # Lock for thread-safe period reset
        reset_lock = asyncio.Lock()
        
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal period_start
            
            # Check if we need to reset the period
            async with reset_lock:
                current_time = time.monotonic()
                if current_time - period_start >= period_seconds:
                    # Reset the period and release all semaphore slots
                    period_start = current_time
                    # Reset semaphore by creating a new one
                    nonlocal semaphore
                    semaphore = asyncio.Semaphore(max_calls)
            
            # Acquire a slot from the semaphore (will wait if limit reached)
            async with semaphore:
                # Execute the original function
                return await func(*args, **kwargs)
                
        return cast(F, wrapper)
        
    return decorator
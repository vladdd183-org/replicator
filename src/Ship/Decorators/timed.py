"""Decorators for the Ship framework."""

import time
from functools import wraps
from typing import Any, Callable, TypeVar, cast

import structlog

logger = structlog.get_logger()

F = TypeVar("F", bound=Callable[..., Any])


def timed(func: F) -> F:
    """Decorator that measures and logs execution time of async functions.
    
    Logs execution time in milliseconds using structlog at INFO level.
    Handles exceptions by logging the duration before re-raising.
    
    Args:
        func: The async function to wrap
        
    Returns:
        The wrapped function that logs execution time
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        
        try:
            result = await func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            await logger.ainfo(
                "timed",
                function=func.__name__,
                duration_ms=duration_ms,
                args=args,
                kwargs=kwargs,
            )
            
            return result
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            await logger.ainfo(
                "timed",
                function=func.__name__,
                duration_ms=duration_ms,
                args=args,
                kwargs=kwargs,
                exception=str(e),
            )
            
            raise
    
    return cast(F, wrapper)

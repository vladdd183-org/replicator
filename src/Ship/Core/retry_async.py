"""Async retry decorator with exponential backoff.

This module provides a decorator for retrying async functions with exponential backoff.
"""

import asyncio
import functools
import logging
from typing import Any, Callable, Optional, Type, TypeVar, Union, cast

from result import Err, Ok, Result

logger = logging.getLogger(__name__)

T = TypeVar("T")
E = TypeVar("E", bound=Exception)
AsyncFunc = TypeVar("AsyncFunc", bound=Callable[..., Any])


def retry_async(
    *,
    base_delay: float = 1.0,
    max_retries: int = 3,
    max_delay: float = 60.0,
    exceptions: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception,
) -> Callable[[AsyncFunc], AsyncFunc]:
    """Decorator that retries async functions with exponential backoff.

    Args:
        base_delay: Initial delay between retries in seconds. Defaults to 1.0.
        max_retries: Maximum number of retry attempts. Defaults to 3.
        max_delay: Maximum delay between retries in seconds. Defaults to 60.0.
        exceptions: Exception types to catch and retry. Defaults to Exception.

    Returns:
        Decorated async function that implements retry logic.

    Example:
        >>> @retry_async(base_delay=0.5, max_retries=3)
        ... async def flaky_operation():
        ...     # Some operation that might fail
        ...     pass

    The delay between retries follows exponential backoff:
    - 1st retry: base_delay seconds
    - 2nd retry: min(base_delay * 2, max_delay) seconds
    - 3rd retry: min(base_delay * 4, max_delay) seconds
    - etc.
    """

    def decorator(func: AsyncFunc) -> AsyncFunc:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            f"Function {func.__name__} succeeded after {attempt} retries"
                        )
                    return result
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    try:
                        await asyncio.sleep(delay)
                    except asyncio.CancelledError:
                        logger.info(f"Retry for {func.__name__} was cancelled")
                        raise
            
            # This should never be reached due to the raise in the loop
            if last_exception:
                raise last_exception
            
            raise RuntimeError("Unexpected state in retry logic")
        
        return cast(AsyncFunc, wrapper)
    
    return decorator


def retry_async_result(
    *,
    base_delay: float = 1.0,
    max_retries: int = 3,
    max_delay: float = 60.0,
    exceptions: Union[Type[Exception], tuple[Type[Exception], ...]] = Exception,
) -> Callable[[Callable[..., Result[T, E]]], Callable[..., Result[T, E]]]:
    """Decorator that retries async functions returning Result with exponential backoff.

    This variant is specifically for functions that return Result[T, E] types.
    It will retry on exceptions but not on Err results.

    Args:
        base_delay: Initial delay between retries in seconds. Defaults to 1.0.
        max_retries: Maximum number of retry attempts. Defaults to 3.
        max_delay: Maximum delay between retries in seconds. Defaults to 60.0.
        exceptions: Exception types to catch and retry. Defaults to Exception.

    Returns:
        Decorated async function that implements retry logic for Result types.
    """

    def decorator(
        func: Callable[..., Result[T, E]]
    ) -> Callable[..., Result[T, E]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Result[T, E]:
            last_exception: Optional[Exception] = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            f"Function {func.__name__} succeeded after {attempt} retries"
                        )
                    return result
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        # Return Err with the exception
                        return Err(cast(E, e))
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    try:
                        await asyncio.sleep(delay)
                    except asyncio.CancelledError:
                        logger.info(f"Retry for {func.__name__} was cancelled")
                        raise
            
            # This should never be reached
            if last_exception:
                return Err(cast(E, last_exception))
            
            return Err(cast(E, RuntimeError("Unexpected state in retry logic")))
        
        return wrapper
    
    return decorator
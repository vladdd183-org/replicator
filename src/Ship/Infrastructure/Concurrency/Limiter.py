"""Rate and concurrency limiters using anyio.

Provides utilities for limiting concurrent operations and rate limiting.
"""

import time
from dataclasses import dataclass, field
from typing import TypeVar, Callable, Awaitable
import anyio

T = TypeVar("T")


@dataclass
class ConcurrencyLimiter:
    """Limit the number of concurrent operations.
    
    Uses anyio.Semaphore under the hood for structured concurrency.
    
    Example:
        limiter = ConcurrencyLimiter(max_concurrent=5)
        
        async with limiter:
            await expensive_operation()
    """
    
    max_concurrent: int
    _semaphore: anyio.Semaphore = field(init=False)
    
    def __post_init__(self) -> None:
        self._semaphore = anyio.Semaphore(self.max_concurrent)
    
    async def __aenter__(self) -> "ConcurrencyLimiter":
        await self._semaphore.__aenter__()
        return self
    
    async def __aexit__(self, *args) -> None:
        await self._semaphore.__aexit__(*args)
    
    async def run(self, func: Callable[[], Awaitable[T]]) -> T:
        """Run function with concurrency limit.
        
        Args:
            func: Async callable to run
            
        Returns:
            Result of the function
        """
        async with self:
            return await func()


@dataclass
class RateLimiter:
    """Token bucket rate limiter.
    
    Limits operations to max_rate per time_window seconds.
    
    Example:
        limiter = RateLimiter(max_rate=10, time_window=1.0)  # 10 ops/sec
        
        for item in items:
            await limiter.acquire()
            await process(item)
    """
    
    max_rate: int
    time_window: float = 1.0  # seconds
    _tokens: float = field(init=False)
    _last_update: float = field(init=False)
    _lock: anyio.Lock = field(init=False)
    
    def __post_init__(self) -> None:
        self._tokens = float(self.max_rate)
        self._last_update = time.monotonic()
        self._lock = anyio.Lock()
    
    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary.
        
        Blocks until a token is available.
        """
        async with self._lock:
            await self._refill()
            
            while self._tokens < 1:
                # Wait for token to become available
                wait_time = self.time_window / self.max_rate
                await anyio.sleep(wait_time)
                await self._refill()
            
            self._tokens -= 1
    
    async def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update
        self._tokens = min(
            self.max_rate,
            self._tokens + (elapsed * self.max_rate / self.time_window),
        )
        self._last_update = now
    
    async def run(self, func: Callable[[], Awaitable[T]]) -> T:
        """Run function with rate limit.
        
        Args:
            func: Async callable to run
            
        Returns:
            Result of the function
        """
        await self.acquire()
        return await func()




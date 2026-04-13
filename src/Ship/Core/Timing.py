"""Timing utilities for measuring execution time."""

import time
from typing import Optional


class Timer:
    """Async context manager for measuring execution time.
    
    Usage:
        async with Timer() as t:
            await some_async_operation()
        print(f"Elapsed: {t.elapsed_ms}ms")
    """
    
    def __init__(self) -> None:
        """Initialize the timer."""
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
    
    async def __aenter__(self) -> "Timer":
        """Start the timer on context entry.
        
        Returns:
            Timer: Self reference for accessing elapsed time.
        """
        self._start_time = time.perf_counter()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop the timer on context exit.
        
        Args:
            exc_type: Exception type if raised.
            exc_val: Exception value if raised.
            exc_tb: Exception traceback if raised.
        """
        self._end_time = time.perf_counter()
    
    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds.
        
        Returns:
            float: Elapsed time in milliseconds.
            
        Raises:
            RuntimeError: If timer hasn't been started or stopped.
        """
        if self._start_time is None:
            raise RuntimeError("Timer hasn't been started")
        if self._end_time is None:
            raise RuntimeError("Timer hasn't been stopped")
        
        elapsed_seconds = self._end_time - self._start_time
        return elapsed_seconds * 1000.0

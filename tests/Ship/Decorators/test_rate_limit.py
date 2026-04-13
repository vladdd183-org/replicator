"""Tests for the rate_limit decorator."""

import asyncio
import time
from typing import List

import pytest

from src.Ship.Decorators import rate_limit


class TestRateLimit:
    """Test cases for rate_limit decorator."""
    
    async def test_normal_operation_within_limits(self) -> None:
        """Test that calls within the limit execute immediately."""
        call_times: List[float] = []
        
        @rate_limit(max_calls=3, period_seconds=1.0)
        async def limited_func() -> str:
            call_times.append(time.monotonic())
            await asyncio.sleep(0.01)  # Simulate some work
            return "success"
        
        # Make 3 calls (within limit)
        tasks = [limited_func() for _ in range(3)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(r == "success" for r in results)
        assert len(call_times) == 3
        
        # All calls should happen almost immediately (within 0.1s)
        duration = call_times[-1] - call_times[0]
        assert duration < 0.1
    
    async def test_throttling_when_limit_exceeded(self) -> None:
        """Test that calls exceeding the limit are delayed."""
        call_times: List[float] = []
        
        @rate_limit(max_calls=2, period_seconds=0.5)
        async def limited_func(idx: int) -> int:
            call_times.append((idx, time.monotonic()))
            return idx
        
        # Start 4 concurrent calls (exceeds limit of 2)
        start_time = time.monotonic()
        tasks = [limited_func(i) for i in range(4)]
        results = await asyncio.gather(*tasks)
        
        # All should eventually complete
        assert sorted(results) == [0, 1, 2, 3]
        assert len(call_times) == 4
        
        # Sort by index to check timing
        call_times.sort(key=lambda x: x[0])
        times_only = [t[1] for t in call_times]
        
        # First 2 calls should be immediate
        assert times_only[1] - times_only[0] < 0.1
        
        # Calls 3 and 4 should be delayed (but not by full period)
        # They should start as soon as the first 2 complete
        assert times_only[2] - start_time < 0.2
        assert times_only[3] - start_time < 0.2
    
    async def test_reset_behavior_after_period(self) -> None:
        """Test that the rate limit resets after the period expires."""
        call_count = 0
        
        @rate_limit(max_calls=2, period_seconds=0.2)
        async def limited_func() -> int:
            nonlocal call_count
            call_count += 1
            return call_count
        
        # First batch: use up the limit
        batch1 = await asyncio.gather(limited_func(), limited_func())
        assert batch1 == [1, 2]
        
        # Wait for period to expire
        await asyncio.sleep(0.25)
        
        # Second batch: should work immediately (limit reset)
        start_time = time.monotonic()
        batch2 = await asyncio.gather(limited_func(), limited_func())
        duration = time.monotonic() - start_time
        
        assert batch2 == [3, 4]
        assert duration < 0.1  # Should be immediate
    
    async def test_concurrent_calls_safety(self) -> None:
        """Test that concurrent calls are handled safely."""
        results: List[int] = []
        
        @rate_limit(max_calls=5, period_seconds=1.0)
        async def limited_func(value: int) -> int:
            await asyncio.sleep(0.01)  # Simulate work
            results.append(value)
            return value
        
        # Launch 10 concurrent tasks
        tasks = [limited_func(i) for i in range(10)]
        returned = await asyncio.gather(*tasks)
        
        # All tasks should complete
        assert len(returned) == 10
        assert sorted(returned) == list(range(10))
        assert len(results) == 10
    
    async def test_preserves_function_signature(self) -> None:
        """Test that the decorator preserves the original function's signature."""
        @rate_limit(max_calls=1, period_seconds=1.0)
        async def func_with_args(a: int, b: str, *, c: float = 1.0) -> tuple:
            return (a, b, c)
        
        result = await func_with_args(42, "test", c=2.5)
        assert result == (42, "test", 2.5)
        
        # Check function metadata is preserved
        assert func_with_args.__name__ == "func_with_args"
    
    async def test_multiple_decorated_functions_independent(self) -> None:
        """Test that multiple decorated functions have independent rate limits."""
        func1_calls = 0
        func2_calls = 0
        
        @rate_limit(max_calls=1, period_seconds=0.5)
        async def func1() -> str:
            nonlocal func1_calls
            func1_calls += 1
            return "func1"
        
        @rate_limit(max_calls=2, period_seconds=0.5)
        async def func2() -> str:
            nonlocal func2_calls
            func2_calls += 1
            return "func2"
        
        # func1 allows 1 call, func2 allows 2 calls
        results = await asyncio.gather(
            func1(),
            func2(),
            func2(),
        )
        
        assert results == ["func1", "func2", "func2"]
        assert func1_calls == 1
        assert func2_calls == 2
    
    def test_decorator_rejects_non_async_functions(self) -> None:
        """Test that the decorator raises TypeError for non-async functions."""
        with pytest.raises(TypeError, match="can only be applied to async functions"):
            @rate_limit(max_calls=1, period_seconds=1.0)
            def sync_func() -> str:
                return "sync"
    
    async def test_zero_period_seconds(self) -> None:
        """Test behavior with zero period (immediate reset)."""
        call_count = 0
        
        @rate_limit(max_calls=1, period_seconds=0.0)
        async def limited_func() -> int:
            nonlocal call_count
            call_count += 1
            return call_count
        
        # Even with max_calls=1, we should be able to make multiple calls
        # because period resets immediately
        results = await asyncio.gather(
            limited_func(),
            limited_func(),
            limited_func(),
        )
        
        assert len(results) == 3
        assert call_count == 3
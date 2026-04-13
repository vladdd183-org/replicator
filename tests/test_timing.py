"""Tests for the Timer context manager."""

import asyncio
import pytest

from src.Ship.Core.Timing import Timer


class TestTimer:
    """Test cases for Timer context manager."""
    
    @pytest.mark.asyncio
    async def test_timer_measures_sleep_duration(self):
        """Test that Timer correctly measures async sleep duration."""
        sleep_duration_ms = 10  # 10ms
        
        async with Timer() as t:
            await asyncio.sleep(sleep_duration_ms / 1000.0)
        
        # Check that elapsed time is greater than 0
        assert t.elapsed_ms > 0
        
        # Check that elapsed time is at least the sleep duration
        # (allowing some tolerance for timing precision)
        assert t.elapsed_ms >= sleep_duration_ms * 0.9
    
    @pytest.mark.asyncio
    async def test_timer_elapsed_ms_attribute_exists(self):
        """Test that Timer has elapsed_ms attribute after context exit."""
        async with Timer() as t:
            await asyncio.sleep(0.001)  # 1ms sleep
        
        # Verify elapsed_ms attribute exists and is accessible
        assert hasattr(t, 'elapsed_ms')
        assert isinstance(t.elapsed_ms, float)
    
    @pytest.mark.asyncio
    async def test_timer_measures_multiple_operations(self):
        """Test Timer with multiple async operations."""
        async with Timer() as t:
            await asyncio.sleep(0.005)  # 5ms
            await asyncio.sleep(0.005)  # 5ms
        
        # Total should be at least 10ms
        assert t.elapsed_ms >= 10.0 * 0.9
    
    @pytest.mark.asyncio
    async def test_timer_works_with_exception(self):
        """Test that Timer still records time when exception occurs."""
        with pytest.raises(ValueError):
            async with Timer() as t:
                await asyncio.sleep(0.001)
                raise ValueError("Test exception")
        
        # Timer should still have recorded elapsed time
        assert t.elapsed_ms > 0
    
    @pytest.mark.asyncio
    async def test_timer_elapsed_ms_before_start(self):
        """Test that accessing elapsed_ms before starting raises error."""
        t = Timer()
        
        with pytest.raises(RuntimeError, match="Timer hasn't been started"):
            _ = t.elapsed_ms
    
    @pytest.mark.asyncio
    async def test_timer_elapsed_ms_before_stop(self):
        """Test that accessing elapsed_ms before stopping raises error."""
        t = Timer()
        await t.__aenter__()
        
        with pytest.raises(RuntimeError, match="Timer hasn't been stopped"):
            _ = t.elapsed_ms
        
        # Clean up
        await t.__aexit__(None, None, None)
    
    @pytest.mark.asyncio
    async def test_timer_precision(self):
        """Test that Timer has millisecond precision."""
        async with Timer() as t:
            # Very short operation
            pass
        
        # Should measure something, even for very fast operations
        assert t.elapsed_ms >= 0
        assert isinstance(t.elapsed_ms, float)
    
    @pytest.mark.asyncio
    async def test_multiple_timer_instances(self):
        """Test that multiple Timer instances work independently."""
        async with Timer() as t1:
            await asyncio.sleep(0.01)  # 10ms
            
            async with Timer() as t2:
                await asyncio.sleep(0.005)  # 5ms
            
            assert t2.elapsed_ms >= 5.0 * 0.9
            assert t2.elapsed_ms < t1.elapsed_ms  # t2 should be less than t1
        
        assert t1.elapsed_ms >= 15.0 * 0.9  # t1 includes both sleeps

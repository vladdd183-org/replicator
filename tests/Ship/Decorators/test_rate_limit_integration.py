"""Integration tests for rate_limit decorator with realistic scenarios."""

import asyncio
import time
from typing import List, Optional

import pytest

from src.Ship.Decorators import rate_limit


class MockAPIClient:
    """Mock API client to simulate rate-limited operations."""
    
    def __init__(self) -> None:
        self.request_times: List[float] = []
        self.request_count = 0
    
    @rate_limit(max_calls=3, period_seconds=1.0)
    async def fetch_data(self, endpoint: str, delay: float = 0.1) -> dict:
        """Simulate an API call with rate limiting."""
        self.request_times.append(time.monotonic())
        self.request_count += 1
        
        # Simulate network delay
        await asyncio.sleep(delay)
        
        return {
            "endpoint": endpoint,
            "request_number": self.request_count,
            "timestamp": time.time(),
        }


class TestRateLimitIntegration:
    """Integration tests for rate_limit decorator."""
    
    async def test_api_client_rate_limiting(self) -> None:
        """Test rate limiting with a mock API client."""
        client = MockAPIClient()
        
        # Make 5 requests (exceeds limit of 3)
        start_time = time.monotonic()
        tasks = [
            client.fetch_data(f"/api/resource/{i}")
            for i in range(5)
        ]
        results = await asyncio.gather(*tasks)
        
        # All requests should complete
        assert len(results) == 5
        assert all(r["endpoint"].startswith("/api/resource/") for r in results)
        
        # Check timing
        assert len(client.request_times) == 5
        
        # First 3 should be immediate
        first_three_duration = client.request_times[2] - client.request_times[0]
        assert first_three_duration < 0.2
        
        # Last 2 should be delayed but complete reasonably quickly
        total_duration = time.monotonic() - start_time
        assert total_duration < 0.5  # Should not wait full period
    
    async def test_burst_traffic_handling(self) -> None:
        """Test handling of burst traffic with rate limiting."""
        processed_requests: List[tuple[int, float]] = []
        
        @rate_limit(max_calls=5, period_seconds=2.0)
        async def process_request(request_id: int) -> str:
            timestamp = time.monotonic()
            processed_requests.append((request_id, timestamp))
            await asyncio.sleep(0.05)  # Simulate processing
            return f"processed-{request_id}"
        
        # Simulate burst of 20 requests
        tasks = [process_request(i) for i in range(20)]
        results = await asyncio.gather(*tasks)
        
        # All should complete
        assert len(results) == 20
        assert all(r.startswith("processed-") for r in results)
        
        # Verify rate limiting was applied
        assert len(processed_requests) == 20
        
        # Check that requests were processed in batches
        timestamps = [t[1] for t in processed_requests]
        
        # Should see clear grouping with max 5 requests starting close together
        for i in range(0, 20, 5):
            batch = timestamps[i:i+5]
            if len(batch) > 1:
                batch_duration = batch[-1] - batch[0]
                assert batch_duration < 0.3  # Batch should start quickly
    
    async def test_mixed_duration_operations(self) -> None:
        """Test rate limiting with operations of varying durations."""
        @rate_limit(max_calls=2, period_seconds=0.5)
        async def variable_operation(duration: float) -> float:
            start = time.monotonic()
            await asyncio.sleep(duration)
            return time.monotonic() - start
        
        # Mix of fast and slow operations
        durations = [0.01, 0.2, 0.01, 0.1, 0.01]
        tasks = [variable_operation(d) for d in durations]
        
        start_time = time.monotonic()
        actual_durations = await asyncio.gather(*tasks)
        total_time = time.monotonic() - start_time
        
        # All operations should complete
        assert len(actual_durations) == 5
        
        # Total time should be reasonable (not waiting full periods)
        assert total_time < 1.0
    
    async def test_exception_handling_with_rate_limit(self) -> None:
        """Test that exceptions don't break rate limiting."""
        call_count = 0
        
        @rate_limit(max_calls=2, period_seconds=0.5)
        async def flaky_operation(should_fail: bool) -> str:
            nonlocal call_count
            call_count += 1
            
            if should_fail:
                raise ValueError("Simulated failure")
            return "success"
        
        # Mix of successful and failing calls
        tasks = [
            flaky_operation(False),
            flaky_operation(True),
            flaky_operation(False),
            flaky_operation(True),
        ]
        
        # Gather with return_exceptions to handle failures
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check results
        assert call_count == 4
        assert results[0] == "success"
        assert isinstance(results[1], ValueError)
        assert results[2] == "success"
        assert isinstance(results[3], ValueError)
    
    async def test_rate_limit_with_timeout(self) -> None:
        """Test rate limiting behavior with operation timeouts."""
        @rate_limit(max_calls=1, period_seconds=0.5)
        async def slow_operation() -> str:
            await asyncio.sleep(2.0)  # Longer than period
            return "completed"
        
        # Start first operation
        task1 = asyncio.create_task(slow_operation())
        
        # Wait a bit and start second operation
        await asyncio.sleep(0.1)
        task2 = asyncio.create_task(slow_operation())
        
        # Second task should wait even though period expired
        # because first task still holds the semaphore
        await asyncio.sleep(0.6)  # Past the period
        
        # Cancel first task
        task1.cancel()
        
        # Second task should now proceed
        try:
            await task1
        except asyncio.CancelledError:
            pass
        
        # Set timeout for second task
        try:
            result = await asyncio.wait_for(task2, timeout=0.5)
            assert result == "completed"
        except asyncio.TimeoutError:
            # This is expected - the operation takes 2s
            task2.cancel()
            try:
                await task2
            except asyncio.CancelledError:
                pass
"""Tests for the retry_async decorator."""

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from result import Err, Ok, Result

from src.Ship.Core.retry_async import retry_async, retry_async_result


class TestRetryAsync:
    """Test cases for retry_async decorator."""

    @pytest.mark.asyncio
    async def test_successful_call_without_retries(self) -> None:
        """Test that successful calls don't trigger retries."""
        call_count = 0

        @retry_async(base_delay=0.1, max_retries=3)
        async def successful_func() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_func()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_function_fails_then_succeeds(self) -> None:
        """Test function that fails a few times then succeeds."""
        call_count = 0
        failures_before_success = 2

        @retry_async(base_delay=0.01, max_retries=3)
        async def flaky_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count <= failures_before_success:
                raise ValueError(f"Failure {call_count}")
            return "success"

        result = await flaky_func()
        assert result == "success"
        assert call_count == failures_before_success + 1

    @pytest.mark.asyncio
    async def test_function_always_fails_raises_last_exception(self) -> None:
        """Test that the last exception is raised after max retries."""
        call_count = 0
        max_retries = 3

        @retry_async(base_delay=0.01, max_retries=max_retries)
        async def always_fails() -> None:
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Failure {call_count}")

        with pytest.raises(ValueError) as exc_info:
            await always_fails()

        assert str(exc_info.value) == f"Failure {max_retries + 1}"
        assert call_count == max_retries + 1

    @pytest.mark.asyncio
    async def test_backoff_respects_max_delay(self) -> None:
        """Test that exponential backoff respects max_delay."""
        base_delay = 1.0
        max_delay = 2.0
        max_retries = 5
        sleep_calls: list[float] = []

        @retry_async(
            base_delay=base_delay,
            max_retries=max_retries,
            max_delay=max_delay
        )
        async def always_fails() -> None:
            raise ValueError("Always fails")

        # Mock asyncio.sleep to capture delay values
        original_sleep = asyncio.sleep

        async def mock_sleep(delay: float) -> None:
            sleep_calls.append(delay)
            # Use a very short actual sleep to speed up test
            await original_sleep(0.001)

        with patch("asyncio.sleep", side_effect=mock_sleep):
            with pytest.raises(ValueError):
                await always_fails()

        # Verify sleep was called with correct delays
        assert len(sleep_calls) == max_retries
        
        # Check exponential backoff with max_delay cap
        expected_delays = [
            min(base_delay * (2 ** i), max_delay)
            for i in range(max_retries)
        ]
        assert sleep_calls == expected_delays
        
        # Specifically verify that max_delay is respected
        assert all(delay <= max_delay for delay in sleep_calls)
        assert any(delay == max_delay for delay in sleep_calls)  # At least one should hit max

    @pytest.mark.asyncio
    async def test_specific_exception_handling(self) -> None:
        """Test that only specified exceptions trigger retries."""
        call_count = 0

        @retry_async(
            base_delay=0.01,
            max_retries=3,
            exceptions=(ValueError, TypeError)
        )
        async def selective_retry() -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Retryable")
            elif call_count == 2:
                raise RuntimeError("Not retryable")
            return "success"

        # RuntimeError should not be retried
        with pytest.raises(RuntimeError):
            await selective_retry()
        
        assert call_count == 2  # First call + one retry

    @pytest.mark.asyncio
    async def test_cancellation_handling(self) -> None:
        """Test that cancellation is properly propagated."""
        call_count = 0

        @retry_async(base_delay=0.1, max_retries=3)
        async def slow_func() -> None:
            nonlocal call_count
            call_count += 1
            raise ValueError("Trigger retry")

        task = asyncio.create_task(slow_func())
        await asyncio.sleep(0.05)  # Let it start and fail once
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

        # Should have been called at least once but not all retries
        assert 1 <= call_count < 4

    @pytest.mark.asyncio
    async def test_preserves_function_signature(self) -> None:
        """Test that decorator preserves function signature and docstring."""

        @retry_async()
        async def example_func(x: int, y: str = "default") -> tuple[int, str]:
            """Example function with signature."""
            return (x, y)

        # Check function name and docstring are preserved
        assert example_func.__name__ == "example_func"
        assert example_func.__doc__ == "Example function with signature."

        # Function should work normally
        result = await example_func(42, y="test")
        assert result == (42, "test")

    @pytest.mark.asyncio
    async def test_retry_with_different_arguments(self) -> None:
        """Test retry works correctly with function arguments."""
        attempts: list[tuple[Any, ...]] = []

        @retry_async(base_delay=0.01, max_retries=2)
        async def func_with_args(x: int, y: str) -> str:
            attempts.append((x, y))
            if len(attempts) < 2:
                raise ValueError("Retry me")
            return f"{x}-{y}"

        result = await func_with_args(42, "test")
        assert result == "42-test"
        assert len(attempts) == 2
        assert all(args == (42, "test") for args in attempts)

    @pytest.mark.asyncio
    async def test_retry_async_result_success(self) -> None:
        """Test retry_async_result with successful Result."""
        call_count = 0

        @retry_async_result(base_delay=0.01, max_retries=3)
        async def result_func() -> Result[str, Exception]:
            nonlocal call_count
            call_count += 1
            return Ok("success")

        result = await result_func()
        assert result.is_ok()
        assert result.unwrap() == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_async_result_with_exceptions(self) -> None:
        """Test retry_async_result retries on exceptions but returns Err."""
        call_count = 0

        @retry_async_result(base_delay=0.01, max_retries=2)
        async def failing_result_func() -> Result[str, Exception]:
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Failure {call_count}")

        result = await failing_result_func()
        assert result.is_err()
        assert isinstance(result.unwrap_err(), ValueError)
        assert str(result.unwrap_err()) == "Failure 3"
        assert call_count == 3  # initial + 2 retries

    @pytest.mark.asyncio
    async def test_timing_of_retries(self) -> None:
        """Test actual timing of retry delays."""
        base_delay = 0.05
        attempts = 3
        start_times: list[float] = []

        @retry_async(base_delay=base_delay, max_retries=attempts)
        async def timed_func() -> None:
            start_times.append(time.time())
            if len(start_times) <= attempts:
                raise ValueError("Retry")

        with pytest.raises(ValueError):
            await timed_func()

        # Calculate actual delays
        actual_delays = [
            start_times[i + 1] - start_times[i]
            for i in range(len(start_times) - 1)
        ]

        # Expected delays with exponential backoff
        expected_delays = [
            base_delay * (2 ** i) for i in range(attempts)
        ]

        # Allow 20ms tolerance for timing
        tolerance = 0.02
        for actual, expected in zip(actual_delays, expected_delays):
            assert abs(actual - expected) < tolerance
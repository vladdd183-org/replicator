"""Task group utilities for structured concurrency.

Uses anyio for structured concurrency - all tasks complete or cancel together.
"""

from typing import TypeVar, Callable, Awaitable, Sequence
import anyio

T = TypeVar("T")
R = TypeVar("R")


async def run_concurrent(*tasks: Callable[[], Awaitable[T]]) -> list[T]:
    """Run multiple async tasks concurrently.
    
    All tasks will complete or cancel together (structured concurrency).
    Results are returned in the same order as input tasks.
    
    Args:
        *tasks: Async callables to run concurrently
        
    Returns:
        List of results in input order
        
    Example:
        results = await run_concurrent(
            lambda: fetch_user(1),
            lambda: fetch_user(2),
            lambda: fetch_user(3),
        )
    """
    results: list[T | None] = [None] * len(tasks)
    
    async def run_indexed(index: int, task: Callable[[], Awaitable[T]]) -> None:
        results[index] = await task()
    
    async with anyio.create_task_group() as tg:
        for i, task in enumerate(tasks):
            tg.start_soon(run_indexed, i, task)
    
    return results  # type: ignore


async def map_concurrent(
    func: Callable[[T], Awaitable[R]],
    items: Sequence[T],
    *,
    max_concurrent: int | None = None,
) -> list[R]:
    """Map an async function over items concurrently.
    
    Args:
        func: Async function to apply to each item
        items: Items to process
        max_concurrent: Maximum concurrent tasks (None = unlimited)
        
    Returns:
        List of results in input order
        
    Example:
        users = await map_concurrent(
            fetch_user,
            [1, 2, 3, 4, 5],
            max_concurrent=3,
        )
    """
    results: list[R | None] = [None] * len(items)
    
    if max_concurrent is not None:
        limiter = anyio.Semaphore(max_concurrent)
    else:
        limiter = None
    
    async def process(index: int, item: T) -> None:
        if limiter is not None:
            async with limiter:
                results[index] = await func(item)
        else:
            results[index] = await func(item)
    
    async with anyio.create_task_group() as tg:
        for i, item in enumerate(items):
            tg.start_soon(process, i, item)
    
    return results  # type: ignore




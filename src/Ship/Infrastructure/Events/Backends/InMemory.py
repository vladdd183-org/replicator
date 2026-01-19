"""In-Memory Event Bus for development and testing.

Provides a simple, fast event bus using asyncio.Queue.
Perfect for local development and unit tests.

Features:
- Zero external dependencies
- Instant event delivery
- Full Protocol compliance
- Ordered delivery (FIFO)
- Support for multiple handlers
"""

from dataclasses import dataclass, field

import anyio
from anyio import move_on_after
from anyio.abc import TaskGroup

import logfire

from src.Ship.Infrastructure.Events.Backends.Base import BaseEventBus
from src.Ship.Infrastructure.Events.Models import (
    EventEnvelope,
)


@dataclass
class InMemoryEventBus(BaseEventBus):
    """In-Memory Event Bus implementation.
    
    Uses asyncio.Queue for event storage and delivery.
    Events are processed by a background consumer task.
    
    Configuration:
        max_queue_size: Maximum events in queue (0 = unlimited)
        process_timeout: Timeout for processing single event
    
    Example:
        event_bus = InMemoryEventBus()
        await event_bus.start()
        
        @subscribe("UserCreated")
        async def on_user_created(event_name: str, payload: dict) -> None:
            print(f"User created: {payload['user_id']}")
        
        await event_bus.subscribe("UserCreated", on_user_created)
        await event_bus.publish("UserCreated", {"user_id": "123"})
        
        await event_bus.stop()
    """
    
    # Configuration
    max_queue_size: int = field(default=0)  # 0 = unlimited
    process_timeout: float = field(default=30.0)
    
    # Internal state
    _queue: anyio.abc.ObjectReceiveStream[EventEnvelope] | None = field(default=None, init=False)
    _send_stream: anyio.abc.ObjectSendStream[EventEnvelope] | None = field(default=None, init=False)
    _task_group: TaskGroup | None = field(default=None, init=False)
    _cancel_scope: anyio.CancelScope | None = field(default=None, init=False)
    _pending_count: int = field(default=0, init=False)
    
    @property
    def backend_type(self) -> str:
        """Get backend type identifier."""
        return "inmemory"
    
    async def _do_start(self) -> None:
        """Initialize queue and start consumer."""
        # Create memory object stream (anyio's async queue)
        self._send_stream, self._queue = anyio.create_memory_object_stream[EventEnvelope](
            max_buffer_size=self.max_queue_size if self.max_queue_size > 0 else float("inf")
        )
        
        # Start consumer in background
        self._cancel_scope = anyio.CancelScope()
        
        # We need to spawn the consumer task
        # Store task group reference for cleanup
        logfire.debug("InMemory event bus: consumer will process events on publish")
    
    async def _do_stop(self) -> None:
        """Stop consumer and cleanup."""
        # Cancel consumer
        if self._cancel_scope:
            self._cancel_scope.cancel()
            self._cancel_scope = None
        
        # Close streams
        if self._send_stream:
            await self._send_stream.aclose()
            self._send_stream = None
        
        if self._queue:
            await self._queue.aclose()
            self._queue = None
    
    async def _do_publish(self, envelope: EventEnvelope) -> None:
        """Publish event to queue and dispatch immediately.
        
        For InMemory backend, we dispatch immediately for simplicity.
        This ensures tests and development see instant results.
        """
        self._pending_count += 1
        
        try:
            # Dispatch directly (synchronous for InMemory)
            await self._dispatch_with_timeout(envelope)
        finally:
            self._pending_count -= 1
    
    async def _dispatch_with_timeout(self, envelope: EventEnvelope) -> None:
        """Dispatch event with timeout protection.
        
        Args:
            envelope: Event to dispatch
        """
        with move_on_after(self.process_timeout) as scope:
            await self.dispatch(envelope)
        
        if scope.cancelled_caught:
            logfire.warning(
                f"⏱️ Event processing timed out: {envelope.event_name}",
                event_name=envelope.event_name,
                timeout=self.process_timeout,
            )
    
    async def _consumer_loop(self) -> None:
        """Background consumer that processes events from queue."""
        if not self._queue:
            return
        
        with self._cancel_scope:
            async for envelope in self._queue:
                await self._dispatch_with_timeout(envelope)
    
    async def _do_health_check(self) -> bool:
        """Check if InMemory bus is healthy.
        
        Returns:
            True (always healthy when running)
        """
        return True
    
    async def wait_for_pending(self, timeout: float = 30.0) -> bool:
        """Wait for pending events to complete.
        
        Args:
            timeout: Maximum wait time
            
        Returns:
            True if all completed
        """
        start = anyio.current_time()
        
        while self._pending_count > 0:
            if anyio.current_time() - start > timeout:
                return False
            await anyio.sleep(0.01)
        
        return True
    
    @property
    def pending_count(self) -> int:
        """Get number of pending events.
        
        Returns:
            Count of events being processed
        """
        return self._pending_count


@dataclass
class InMemoryEventBusWithQueue(BaseEventBus):
    """In-Memory Event Bus with background queue processing.
    
    Alternative implementation that queues events and processes
    them in a background task. Better for high-throughput scenarios.
    
    Example:
        async with anyio.create_task_group() as tg:
            event_bus = InMemoryEventBusWithQueue()
            await event_bus.start(tg)
            
            await event_bus.publish("Test", {"data": "value"})
            
            await event_bus.wait_for_pending()
            await event_bus.stop()
    """
    
    # Configuration
    max_queue_size: int = field(default=10000)
    process_timeout: float = field(default=30.0)
    worker_count: int = field(default=4)
    
    # Internal state
    _queue: anyio.abc.ObjectReceiveStream[EventEnvelope] | None = field(default=None, init=False)
    _send_stream: anyio.abc.ObjectSendStream[EventEnvelope] | None = field(default=None, init=False)
    _task_group: TaskGroup | None = field(default=None, init=False)
    _stop_event: anyio.Event | None = field(default=None, init=False)
    _pending_count: int = field(default=0, init=False)
    
    @property
    def backend_type(self) -> str:
        return "inmemory-queued"
    
    async def start_with_task_group(self, task_group: TaskGroup) -> None:
        """Start with an external task group.
        
        Args:
            task_group: TaskGroup to spawn workers in
        """
        self._task_group = task_group
        await self._do_start()
        self._running = True
    
    async def _do_start(self) -> None:
        """Initialize queue and start workers."""
        self._send_stream, self._queue = anyio.create_memory_object_stream[EventEnvelope](
            max_buffer_size=self.max_queue_size
        )
        self._stop_event = anyio.Event()
        
        # Start workers if we have a task group
        if self._task_group:
            for i in range(self.worker_count):
                self._task_group.start_soon(self._worker, i)
    
    async def _do_stop(self) -> None:
        """Signal workers to stop and cleanup."""
        if self._stop_event:
            self._stop_event.set()
        
        if self._send_stream:
            await self._send_stream.aclose()
            self._send_stream = None
    
    async def _do_publish(self, envelope: EventEnvelope) -> None:
        """Add event to queue for background processing."""
        if not self._send_stream:
            raise RuntimeError("Event bus not started")
        
        self._pending_count += 1
        await self._send_stream.send(envelope)
    
    async def _worker(self, worker_id: int) -> None:
        """Background worker that processes events.
        
        Args:
            worker_id: Worker identifier for logging
        """
        logfire.debug(f"Worker {worker_id} started")
        
        if not self._queue or not self._stop_event:
            return
        
        try:
            async for envelope in self._queue:
                if self._stop_event.is_set():
                    break
                
                try:
                    with move_on_after(self.process_timeout):
                        await self.dispatch(envelope)
                finally:
                    self._pending_count -= 1
                    
        except anyio.ClosedResourceError:
            pass
        
        logfire.debug(f"Worker {worker_id} stopped")
    
    async def _do_health_check(self) -> bool:
        return True
    
    async def wait_for_pending(self, timeout: float = 30.0) -> bool:
        """Wait for all queued events to be processed."""
        start = anyio.current_time()
        
        while self._pending_count > 0:
            if anyio.current_time() - start > timeout:
                return False
            await anyio.sleep(0.01)
        
        return True


__all__ = ["InMemoryEventBus", "InMemoryEventBusWithQueue"]

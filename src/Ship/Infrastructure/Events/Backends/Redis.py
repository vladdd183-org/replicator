"""Redis Streams Event Bus for production use.

Uses Redis Streams (XADD/XREAD/XREADGROUP) for reliable event delivery.
Supports consumer groups for horizontal scaling.

Features:
- Persistent event storage
- Consumer groups for load balancing
- Message acknowledgment (XACK)
- Automatic retry with exponential backoff
- Dead letter queue via separate stream
- At-least-once delivery guarantee

Requirements:
    pip install redis>=5.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import json

import anyio
from anyio import create_task_group, move_on_after
from anyio.abc import TaskGroup

import logfire

from src.Ship.Infrastructure.Events.Backends.Base import BaseEventBus
from src.Ship.Infrastructure.Events.Errors import (
    EventBusConnectionError,
    EventPublishError,
)
from src.Ship.Infrastructure.Events.Models import (
    DeadLetterEvent,
    EventEnvelope,
    EventMetadata,
    EventPriority,
)


@dataclass
class RedisEventBus(BaseEventBus):
    """Redis Streams Event Bus implementation.
    
    Uses Redis Streams for reliable, scalable event processing.
    
    Configuration:
        redis_url: Redis connection URL
        stream_prefix: Prefix for stream names
        consumer_group: Consumer group name
        consumer_name: This consumer's name (unique per instance)
        max_stream_length: Maximum events per stream (MAXLEN ~)
        block_timeout_ms: Timeout for XREAD blocking
        batch_size: Events to read per batch
        claim_min_idle_ms: Min idle time before claiming pending message
    
    Stream naming:
        events:{event_name} - Main event stream
        events:dlq - Dead letter queue stream
    
    Example:
        event_bus = RedisEventBus(
            redis_url="redis://localhost:6379/0",
            consumer_group="my-service",
            consumer_name="worker-1",
        )
        
        await event_bus.start()
        await event_bus.subscribe("UserCreated", handler)
        await event_bus.publish("UserCreated", {"user_id": "123"})
    """
    
    # Connection
    redis_url: str = field(default="redis://localhost:6379/0")
    
    # Stream configuration
    stream_prefix: str = field(default="events")
    consumer_group: str = field(default="default-group")
    consumer_name: str = field(default="")  # Auto-generated if empty
    max_stream_length: int = field(default=100000)
    dlq_stream: str = field(default="events:dlq")
    
    # Consumer configuration
    block_timeout_ms: int = field(default=5000)
    batch_size: int = field(default=10)
    claim_min_idle_ms: int = field(default=60000)
    worker_count: int = field(default=2)
    
    # Internal state
    _redis: Any = field(default=None, init=False)
    _task_group: TaskGroup | None = field(default=None, init=False)
    _stop_event: anyio.Event | None = field(default=None, init=False)
    _subscribed_streams: set[str] = field(default_factory=set, init=False)
    
    def __post_init__(self) -> None:
        """Initialize consumer name if not provided."""
        if not self.consumer_name:
            import uuid
            self.consumer_name = f"consumer-{uuid.uuid4().hex[:8]}"
    
    @property
    def backend_type(self) -> str:
        return "redis"
    
    def _stream_name(self, event_name: str) -> str:
        """Get stream name for an event.
        
        Args:
            event_name: Event name
            
        Returns:
            Redis stream key
        """
        return f"{self.stream_prefix}:{event_name}"
    
    async def _do_start(self) -> None:
        """Connect to Redis and initialize streams."""
        try:
            import redis.asyncio as redis
        except ImportError:
            raise ImportError(
                "redis package required for RedisEventBus. "
                "Install with: pip install redis>=5.0.0"
            )
        
        try:
            self._redis = redis.from_url(
                self.redis_url,
                decode_responses=True,
            )
            
            # Test connection
            await self._redis.ping()
            
            self._stop_event = anyio.Event()
            
            logfire.info(
                "Connected to Redis",
                url=self.redis_url,
                consumer_group=self.consumer_group,
                consumer_name=self.consumer_name,
            )
            
        except Exception as e:
            raise EventBusConnectionError(
                backend_type="redis",
                original_error=str(e),
            )
    
    async def _do_stop(self) -> None:
        """Disconnect from Redis."""
        if self._stop_event:
            self._stop_event.set()
        
        # Wait for workers to finish
        await anyio.sleep(0.1)
        
        if self._redis:
            await self._redis.aclose()
            self._redis = None
    
    async def _ensure_consumer_group(self, stream: str) -> None:
        """Create consumer group if it doesn't exist.
        
        Args:
            stream: Stream name
        """
        try:
            await self._redis.xgroup_create(
                stream,
                self.consumer_group,
                id="0",
                mkstream=True,
            )
        except Exception as e:
            # Group already exists - that's fine
            if "BUSYGROUP" not in str(e):
                raise
    
    async def _do_publish(self, envelope: EventEnvelope) -> None:
        """Publish event to Redis Stream.
        
        Args:
            envelope: Event envelope to publish
        """
        if not self._redis:
            raise EventBusConnectionError(
                backend_type="redis",
                original_error="Not connected",
            )
        
        stream = self._stream_name(envelope.event_name)
        
        # Serialize envelope
        data = {
            "envelope": json.dumps(envelope.to_json()),
            "event_name": envelope.event_name,
            "priority": envelope.metadata.priority.value,
            "timestamp": envelope.metadata.timestamp.isoformat(),
        }
        
        try:
            # XADD with MAXLEN for stream trimming
            await self._redis.xadd(
                stream,
                data,
                maxlen=self.max_stream_length,
            )
            
        except Exception as e:
            raise EventPublishError(
                event_name=envelope.event_name,
                reason=str(e),
                event_id=envelope.metadata.event_id,
            )
    
    async def subscribe(
        self,
        event_name: str,
        handler: Any,
        *,
        group: str | None = None,
    ) -> None:
        """Subscribe to events and start consumer.
        
        Args:
            event_name: Event to subscribe to
            handler: Handler function
            group: Optional consumer group override
        """
        await super().subscribe(event_name, handler, group=group)
        
        stream = self._stream_name(event_name)
        
        if stream not in self._subscribed_streams:
            self._subscribed_streams.add(stream)
            
            # Ensure consumer group exists
            await self._ensure_consumer_group(stream)
            
            # Start worker for this stream if not already running
            # Workers are started when start() is called with task group
    
    async def start_consumers(self, task_group: TaskGroup) -> None:
        """Start consumer workers in the given task group.
        
        Call this after subscribing to events.
        
        Args:
            task_group: TaskGroup to spawn workers in
        """
        self._task_group = task_group
        
        for i in range(self.worker_count):
            task_group.start_soon(self._consumer_worker, i)
    
    async def _consumer_worker(self, worker_id: int) -> None:
        """Background worker that consumes from subscribed streams.
        
        Args:
            worker_id: Worker identifier
        """
        if not self._redis or not self._stop_event:
            return
        
        logfire.debug(f"Redis consumer worker {worker_id} started")
        
        while not self._stop_event.is_set():
            try:
                await self._consume_batch()
            except anyio.get_cancelled_exc_class():
                break
            except Exception as e:
                logfire.error(
                    f"Redis consumer error: {e}",
                    worker_id=worker_id,
                    exc_info=True,
                )
                await anyio.sleep(1.0)  # Back off on error
        
        logfire.debug(f"Redis consumer worker {worker_id} stopped")
    
    async def _consume_batch(self) -> None:
        """Consume and process a batch of events."""
        if not self._subscribed_streams or not self._redis:
            await anyio.sleep(0.1)
            return
        
        # Build streams dict for XREADGROUP
        streams = {stream: ">" for stream in self._subscribed_streams}
        
        try:
            # Read new messages
            results = await self._redis.xreadgroup(
                self.consumer_group,
                self.consumer_name,
                streams=streams,
                count=self.batch_size,
                block=self.block_timeout_ms,
            )
            
            if not results:
                return
            
            # Process each message
            for stream_name, messages in results:
                for message_id, data in messages:
                    await self._process_message(stream_name, message_id, data)
                    
        except Exception as e:
            if "NOGROUP" in str(e):
                # Consumer group doesn't exist, recreate
                for stream in self._subscribed_streams:
                    await self._ensure_consumer_group(stream)
            else:
                raise
    
    async def _process_message(
        self,
        stream: str,
        message_id: str,
        data: dict[str, str],
    ) -> None:
        """Process a single message from Redis Stream.
        
        Args:
            stream: Stream name
            message_id: Redis message ID
            data: Message data
        """
        try:
            # Deserialize envelope
            envelope_json = json.loads(data.get("envelope", "{}"))
            envelope = EventEnvelope.from_json(envelope_json)
            
            # Dispatch to handlers
            await self.dispatch(envelope)
            
            # Acknowledge message
            await self._redis.xack(stream, self.consumer_group, message_id)
            
        except Exception as e:
            logfire.error(
                f"Failed to process Redis message: {e}",
                stream=stream,
                message_id=message_id,
            )
            
            # Move to DLQ after max retries
            if envelope and not envelope.metadata.should_retry():
                await self._move_to_dlq(stream, message_id, data, str(e))
                await self._redis.xack(stream, self.consumer_group, message_id)
    
    async def _move_to_dlq(
        self,
        stream: str,
        message_id: str,
        data: dict[str, str],
        error: str,
    ) -> None:
        """Move failed message to dead letter queue.
        
        Args:
            stream: Source stream
            message_id: Original message ID
            data: Message data
            error: Error message
        """
        dlq_data = {
            **data,
            "original_stream": stream,
            "original_message_id": message_id,
            "error": error,
            "failed_at": datetime.now(timezone.utc).isoformat(),
        }
        
        await self._redis.xadd(
            self.dlq_stream,
            dlq_data,
            maxlen=self.max_stream_length,
        )
    
    async def _do_health_check(self) -> bool:
        """Check Redis connection health."""
        if not self._redis:
            return False
        
        try:
            await self._redis.ping()
            return True
        except Exception:
            return False
    
    async def wait_for_pending(self, timeout: float = 30.0) -> bool:
        """Wait for pending messages to be processed.
        
        Note: In Redis Streams, pending messages are tracked server-side.
        This method checks if there are pending messages for this consumer.
        """
        if not self._redis:
            return True
        
        start = anyio.current_time()
        
        while anyio.current_time() - start < timeout:
            has_pending = False
            
            for stream in self._subscribed_streams:
                try:
                    pending = await self._redis.xpending(
                        stream,
                        self.consumer_group,
                    )
                    if pending and pending.get("pending", 0) > 0:
                        has_pending = True
                        break
                except Exception:
                    pass
            
            if not has_pending:
                return True
            
            await anyio.sleep(0.1)
        
        return False
    
    async def claim_pending(self, min_idle_ms: int | None = None) -> int:
        """Claim and reprocess pending messages from dead consumers.
        
        Args:
            min_idle_ms: Minimum idle time for messages to claim
            
        Returns:
            Number of messages claimed
        """
        if not self._redis:
            return 0
        
        min_idle = min_idle_ms or self.claim_min_idle_ms
        claimed = 0
        
        for stream in self._subscribed_streams:
            try:
                # Get pending messages
                pending = await self._redis.xpending_range(
                    stream,
                    self.consumer_group,
                    min="-",
                    max="+",
                    count=100,
                )
                
                for entry in pending:
                    if entry.get("time_since_delivered", 0) >= min_idle:
                        message_id = entry.get("message_id")
                        
                        # Claim the message
                        result = await self._redis.xclaim(
                            stream,
                            self.consumer_group,
                            self.consumer_name,
                            min_idle,
                            [message_id],
                        )
                        
                        if result:
                            claimed += 1
                            # Process claimed message
                            for msg_id, data in result:
                                await self._process_message(stream, msg_id, data)
                                
            except Exception as e:
                logfire.error(f"Error claiming pending messages: {e}")
        
        return claimed


__all__ = ["RedisEventBus"]

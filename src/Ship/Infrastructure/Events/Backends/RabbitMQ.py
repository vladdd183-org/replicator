"""RabbitMQ Event Bus for enterprise use.

Uses aio-pika for async RabbitMQ communication with:
- Topic exchange for flexible routing
- Durable queues for message persistence
- Dead letter exchange for failed messages
- Publisher confirms for reliability
- Consumer prefetch for flow control

Features:
- At-least-once delivery guarantee
- Message persistence
- Dead letter queue
- Consumer groups via competing consumers
- Message TTL and priority
- Automatic reconnection

Requirements:
    pip install aio-pika>=9.0.0
"""

from dataclasses import dataclass, field
from typing import Any
import json

import anyio

import logfire

from src.Ship.Infrastructure.Events.Backends.Base import BaseEventBus
from src.Ship.Infrastructure.Events.Errors import (
    EventBusConnectionError,
    EventPublishError,
)
from src.Ship.Infrastructure.Events.Models import (
    EventEnvelope,
    EventPriority,
)


# Priority mapping to RabbitMQ priority (0-9)
PRIORITY_MAP = {
    EventPriority.LOW: 1,
    EventPriority.NORMAL: 5,
    EventPriority.HIGH: 7,
    EventPriority.CRITICAL: 9,
}


@dataclass
class RabbitMQEventBus(BaseEventBus):
    """RabbitMQ Event Bus implementation.
    
    Uses aio-pika for async AMQP communication.
    
    Configuration:
        rabbitmq_url: AMQP connection URL
        exchange_name: Main exchange name
        exchange_type: Exchange type (topic, direct, fanout)
        queue_prefix: Prefix for queue names
        dlx_exchange: Dead letter exchange name
        dlq_queue: Dead letter queue name
        prefetch_count: Consumer prefetch limit
        message_ttl_ms: Default message TTL
        confirm_delivery: Enable publisher confirms
    
    Routing:
        - Exchange: events (topic)
        - Queue per event: events.{event_name}
        - Routing key: event.{event_name}
        - DLX: events.dlx
        - DLQ: events.dlq
    
    Example:
        event_bus = RabbitMQEventBus(
            rabbitmq_url="amqp://guest:guest@localhost:5672/",
            exchange_name="events",
        )
        
        await event_bus.start()
        await event_bus.subscribe("UserCreated", handler)
        await event_bus.publish("UserCreated", {"user_id": "123"})
    """
    
    # Connection
    rabbitmq_url: str = field(default="amqp://guest:guest@localhost:5672/")
    
    # Exchange configuration
    exchange_name: str = field(default="events")
    exchange_type: str = field(default="topic")
    
    # Queue configuration
    queue_prefix: str = field(default="events")
    dlx_exchange: str = field(default="events.dlx")
    dlq_queue: str = field(default="events.dlq")
    
    # Consumer configuration
    prefetch_count: int = field(default=10)
    consumer_tag_prefix: str = field(default="consumer")
    
    # Message configuration
    message_ttl_ms: int = field(default=86400000)  # 24 hours
    confirm_delivery: bool = field(default=True)
    
    # Internal state
    _connection: Any = field(default=None, init=False)
    _channel: Any = field(default=None, init=False)
    _exchange: Any = field(default=None, init=False)
    _dlx_exchange: Any = field(default=None, init=False)
    _queues: dict[str, Any] = field(default_factory=dict, init=False)
    _consumers: dict[str, Any] = field(default_factory=dict, init=False)
    _stop_event: anyio.Event | None = field(default=None, init=False)
    
    @property
    def backend_type(self) -> str:
        return "rabbitmq"
    
    def _queue_name(self, event_name: str) -> str:
        """Get queue name for an event.
        
        Args:
            event_name: Event name
            
        Returns:
            Queue name
        """
        return f"{self.queue_prefix}.{event_name}"
    
    def _routing_key(self, event_name: str) -> str:
        """Get routing key for an event.
        
        Args:
            event_name: Event name
            
        Returns:
            Routing key
        """
        return f"event.{event_name}"
    
    async def _do_start(self) -> None:
        """Connect to RabbitMQ and setup exchanges/queues."""
        try:
            import aio_pika
        except ImportError:
            raise ImportError(
                "aio-pika package required for RabbitMQEventBus. "
                "Install with: pip install aio-pika>=9.0.0"
            )
        
        try:
            # Connect to RabbitMQ
            self._connection = await aio_pika.connect_robust(
                self.rabbitmq_url,
                reconnect_interval=5,
            )
            
            # Create channel with QoS
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=self.prefetch_count)
            
            # Enable publisher confirms if requested
            if self.confirm_delivery:
                await self._channel.set_qos(prefetch_count=self.prefetch_count)
            
            # Declare main exchange
            self._exchange = await self._channel.declare_exchange(
                self.exchange_name,
                type=aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            
            # Declare dead letter exchange
            self._dlx_exchange = await self._channel.declare_exchange(
                self.dlx_exchange,
                type=aio_pika.ExchangeType.DIRECT,
                durable=True,
            )
            
            # Declare dead letter queue
            dlq = await self._channel.declare_queue(
                self.dlq_queue,
                durable=True,
            )
            await dlq.bind(self._dlx_exchange, routing_key="dead-letter")
            
            self._stop_event = anyio.Event()
            
            logfire.info(
                "Connected to RabbitMQ",
                url=self.rabbitmq_url,
                exchange=self.exchange_name,
            )
            
        except Exception as e:
            raise EventBusConnectionError(
                backend_type="rabbitmq",
                original_error=str(e),
            )
    
    async def _do_stop(self) -> None:
        """Disconnect from RabbitMQ."""
        if self._stop_event:
            self._stop_event.set()
        
        # Cancel all consumers
        for consumer_tag in list(self._consumers.keys()):
            try:
                queue = self._consumers[consumer_tag]
                await queue.cancel(consumer_tag)
            except Exception:
                pass
        
        self._consumers.clear()
        self._queues.clear()
        
        # Close channel and connection
        if self._channel:
            await self._channel.close()
            self._channel = None
        
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def _ensure_queue(self, event_name: str) -> Any:
        """Ensure queue exists for an event.
        
        Args:
            event_name: Event name
            
        Returns:
            Queue object
        """
        queue_name = self._queue_name(event_name)
        
        if queue_name in self._queues:
            return self._queues[queue_name]
        
        try:
            import aio_pika
        except ImportError:
            raise ImportError("aio-pika package required")
        
        # Declare queue with dead letter routing
        queue = await self._channel.declare_queue(
            queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": self.dlx_exchange,
                "x-dead-letter-routing-key": "dead-letter",
                "x-message-ttl": self.message_ttl_ms,
            },
        )
        
        # Bind to exchange
        routing_key = self._routing_key(event_name)
        await queue.bind(self._exchange, routing_key=routing_key)
        
        self._queues[queue_name] = queue
        return queue
    
    async def _do_publish(self, envelope: EventEnvelope) -> None:
        """Publish event to RabbitMQ.
        
        Args:
            envelope: Event envelope to publish
        """
        if not self._exchange:
            raise EventBusConnectionError(
                backend_type="rabbitmq",
                original_error="Not connected",
            )
        
        try:
            import aio_pika
        except ImportError:
            raise ImportError("aio-pika package required")
        
        routing_key = self._routing_key(envelope.event_name)
        
        # Serialize envelope
        body = json.dumps(envelope.to_json()).encode()
        
        # Create message with properties
        message = aio_pika.Message(
            body=body,
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            priority=PRIORITY_MAP.get(envelope.metadata.priority, 5),
            message_id=str(envelope.metadata.event_id),
            timestamp=envelope.metadata.timestamp,
            headers={
                "event_name": envelope.event_name,
                "event_type": envelope.event_type,
                "correlation_id": str(envelope.metadata.correlation_id) if envelope.metadata.correlation_id else None,
                "retry_count": envelope.metadata.retry_count,
            },
        )
        
        try:
            # Publish with optional confirmation
            if self.confirm_delivery:
                await self._exchange.publish(
                    message,
                    routing_key=routing_key,
                    mandatory=True,
                )
            else:
                await self._exchange.publish(
                    message,
                    routing_key=routing_key,
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
        """Subscribe to events from RabbitMQ.
        
        Args:
            event_name: Event to subscribe to
            handler: Handler function
            group: Not used in RabbitMQ (use queue name for competing consumers)
        """
        await super().subscribe(event_name, handler, group=group)
        
        # Ensure queue exists
        queue = await self._ensure_queue(event_name)
        
        # Start consumer if not already consuming
        queue_name = self._queue_name(event_name)
        if queue_name not in self._consumers:
            consumer_tag = f"{self.consumer_tag_prefix}.{event_name}"
            
            async def on_message(message: Any) -> None:
                await self._process_message(event_name, message)
            
            await queue.consume(on_message, consumer_tag=consumer_tag)
            self._consumers[queue_name] = queue
            
            logfire.debug(
                f"Started RabbitMQ consumer for {event_name}",
                queue=queue_name,
                consumer_tag=consumer_tag,
            )
    
    async def _process_message(self, event_name: str, message: Any) -> None:
        """Process a message from RabbitMQ.
        
        Args:
            event_name: Event name
            message: aio-pika IncomingMessage
        """
        try:
            # Deserialize envelope
            body = message.body.decode()
            envelope_json = json.loads(body)
            envelope = EventEnvelope.from_json(envelope_json)
            
            # Dispatch to handlers
            await self.dispatch(envelope)
            
            # Acknowledge message
            await message.ack()
            
        except Exception as e:
            logfire.error(
                f"Failed to process RabbitMQ message: {e}",
                event_name=event_name,
                message_id=message.message_id,
            )
            
            # Check retry count from headers
            headers = message.headers or {}
            retry_count = headers.get("retry_count", 0)
            
            if retry_count >= self.max_dead_letters:
                # Reject and send to DLQ
                await message.reject(requeue=False)
            else:
                # Requeue for retry
                await message.nack(requeue=True)
    
    async def _do_health_check(self) -> bool:
        """Check RabbitMQ connection health."""
        if not self._connection:
            return False
        
        try:
            return not self._connection.is_closed
        except Exception:
            return False
    
    async def wait_for_pending(self, timeout: float = 30.0) -> bool:
        """Wait for pending messages.
        
        Note: RabbitMQ manages message state. This checks queue depths.
        """
        if not self._channel:
            return True
        
        start = anyio.current_time()
        
        while anyio.current_time() - start < timeout:
            all_empty = True
            
            for queue_name, queue in self._queues.items():
                try:
                    # Re-declare to get message count
                    declared = await self._channel.declare_queue(
                        queue_name,
                        passive=True,
                    )
                    if declared.declaration_result.message_count > 0:
                        all_empty = False
                        break
                except Exception:
                    pass
            
            if all_empty:
                return True
            
            await anyio.sleep(0.1)
        
        return False
    
    async def get_dlq_messages(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get messages from dead letter queue.
        
        Args:
            limit: Maximum messages to retrieve
            
        Returns:
            List of DLQ message data
        """
        if not self._channel:
            return []
        
        messages = []
        
        try:
            dlq = await self._channel.declare_queue(
                self.dlq_queue,
                passive=True,
            )
            
            for _ in range(limit):
                message = await dlq.get(no_ack=False)
                if message is None:
                    break
                
                try:
                    body = message.body.decode()
                    data = json.loads(body)
                    data["_rabbitmq"] = {
                        "message_id": message.message_id,
                        "delivery_tag": message.delivery_tag,
                        "headers": dict(message.headers or {}),
                    }
                    messages.append(data)
                    
                    # Don't ack - leave in queue
                    await message.nack(requeue=True)
                except Exception:
                    await message.nack(requeue=True)
                    
        except Exception as e:
            logfire.error(f"Error reading DLQ: {e}")
        
        return messages
    
    async def replay_dlq_message(self, message_id: str) -> bool:
        """Replay a message from DLQ.
        
        Args:
            message_id: Message ID to replay
            
        Returns:
            True if replayed
        """
        if not self._channel:
            return False
        
        try:
            dlq = await self._channel.declare_queue(
                self.dlq_queue,
                passive=True,
            )
            
            # Find and replay the message
            while True:
                message = await dlq.get(no_ack=False)
                if message is None:
                    break
                
                if message.message_id == message_id:
                    # Re-publish to main exchange
                    body = message.body.decode()
                    envelope_json = json.loads(body)
                    
                    # Reset retry count
                    envelope_json["metadata"]["retry_count"] = 0
                    envelope = EventEnvelope.from_json(envelope_json)
                    
                    await self.publish_envelope(envelope)
                    await message.ack()
                    
                    logfire.info(
                        f"Replayed DLQ message: {message_id}",
                        event_name=envelope.event_name,
                    )
                    
                    return True
                else:
                    await message.nack(requeue=True)
                    
        except Exception as e:
            logfire.error(f"Error replaying DLQ message: {e}")
        
        return False


__all__ = ["RabbitMQEventBus"]

"""Event Bus Backends for Hyper-Porto.

Available backends:
- InMemoryEventBus: Development and testing
- RedisEventBus: Production with Redis Streams
- RabbitMQEventBus: Enterprise with RabbitMQ

Usage via Factory (recommended):
    from src.Ship.Infrastructure.Events import create_event_bus
    
    event_bus = create_event_bus(settings)
    
Direct usage:
    from src.Ship.Infrastructure.Events.Backends import InMemoryEventBus
    
    event_bus = InMemoryEventBus()
    await event_bus.start()
"""

from src.Ship.Infrastructure.Events.Backends.InMemory import InMemoryEventBus
from src.Ship.Infrastructure.Events.Backends.Redis import RedisEventBus
from src.Ship.Infrastructure.Events.Backends.RabbitMQ import RabbitMQEventBus
from src.Ship.Infrastructure.Events.Backends.Base import BaseEventBus

__all__ = [
    "BaseEventBus",
    "InMemoryEventBus",
    "RedisEventBus",
    "RabbitMQEventBus",
]

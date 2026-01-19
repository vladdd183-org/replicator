"""TaskIQ Broker configuration with Dishka DI integration.

Configures the broker for background task processing.
Uses Redis as the message queue backend for production.
"""

from taskiq import InMemoryBroker
from taskiq_redis import ListQueueBroker
from dishka import make_async_container
from dishka.integrations.taskiq import setup_dishka

from src.Ship.Configs import get_settings
from src.Ship.Providers import get_worker_providers

settings = get_settings()


def get_broker():
    """Get TaskIQ broker based on environment.
    
    Returns:
        Configured broker instance (Redis for production, InMemory for dev)
    """
    if settings.is_production:
        return ListQueueBroker(settings.redis_url)
    else:
        # Use InMemory broker for development/testing
        return InMemoryBroker()


# Global broker instance
broker = get_broker()

# Setup Dishka DI for TaskIQ
# This enables FromDishka injection in task functions
# NOTE: Workers use CLI-style providers without HTTP Request dependency
_container = make_async_container(*get_worker_providers())
setup_dishka(container=_container, broker=broker)

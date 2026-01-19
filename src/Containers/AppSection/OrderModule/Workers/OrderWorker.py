"""OrderModule Temporal Worker — executes OrderModule workflows and activities.

This worker processes:
- CreateOrderWorkflow (order creation saga)
- All order activities (create, reserve, charge, deliver, notify)

Architecture:
- Worker connects to Temporal server
- Polls "orders" task queue
- Executes workflows and activities

Running:
    # As standalone
    python -m src.Containers.AppSection.OrderModule.Workers.run
    
    # Via CLI
    python -m src.Ship.CLI.Main worker order
    
    # In Docker
    docker-compose up order-worker

Configuration (via Settings):
    TEMPORAL_HOST=localhost:7233
    TEMPORAL_NAMESPACE=default
"""

import asyncio
import anyio
import signal
from dataclasses import dataclass
from typing import Any

from temporalio.client import Client
from temporalio.worker import Worker

from src.Ship.Infrastructure.Temporal import (
    get_temporal_client,
    create_temporal_client,
    TemporalClientConfig,
)
from src.Ship.Configs.Settings import get_settings

# Import workflows and activities
from src.Containers.AppSection.OrderModule.Workflows import (
    ALL_WORKFLOWS,
    TASK_QUEUE,
)
from src.Containers.AppSection.OrderModule.Activities import ALL_ACTIVITIES


# Task queue name
ORDER_TASK_QUEUE = TASK_QUEUE  # "orders"


@dataclass
class OrderWorkerConfig:
    """Configuration for Order Worker.
    
    Attributes:
        task_queue: Temporal task queue name
        max_concurrent_activities: Max parallel activities
        max_concurrent_workflow_tasks: Max parallel workflow tasks
    """
    
    task_queue: str = ORDER_TASK_QUEUE
    max_concurrent_activities: int = 100
    max_concurrent_workflow_tasks: int = 100
    
    @classmethod
    def from_settings(cls) -> "OrderWorkerConfig":
        """Create config from Settings."""
        settings = get_settings()
        return cls(
            task_queue=ORDER_TASK_QUEUE,
            max_concurrent_activities=settings.temporal_max_concurrent_activities,
            max_concurrent_workflow_tasks=settings.temporal_max_concurrent_workflows,
        )


async def create_order_worker(
    client: Client | None = None,
    config: OrderWorkerConfig | None = None,
) -> Worker:
    """Create Order Worker instance.
    
    Args:
        client: Temporal Client (creates new if None)
        config: Worker configuration (uses defaults if None)
        
    Returns:
        Configured Worker instance
        
    Example:
        client = await get_temporal_client()
        worker = await create_order_worker(client)
        await worker.run()
    """
    if client is None:
        client = await get_temporal_client()
    
    if config is None:
        config = OrderWorkerConfig()
    
    worker = Worker(
        client,
        task_queue=config.task_queue,
        workflows=ALL_WORKFLOWS,
        activities=ALL_ACTIVITIES,
        max_concurrent_activities=config.max_concurrent_activities,
        max_concurrent_workflow_task_polls=config.max_concurrent_workflow_tasks,
    )
    
    return worker


async def run_order_worker(
    client: Client | None = None,
    config: OrderWorkerConfig | None = None,
) -> None:
    """Run Order Worker until shutdown.
    
    Sets up signal handlers for graceful shutdown.
    
    Args:
        client: Temporal Client (creates new if None)
        config: Worker configuration (uses defaults if None)
        
    Example:
        # Run with defaults
        await run_order_worker()
        
        # Run with custom config
        config = OrderWorkerConfig(max_concurrent_activities=50)
        await run_order_worker(config=config)
    """
    import logfire
    
    if client is None:
        client = await get_temporal_client()
    
    if config is None:
        config = OrderWorkerConfig()
    
    worker = await create_order_worker(client, config)
    
    # Setup shutdown handling
    shutdown_event = anyio.Event()
    
    def signal_handler(sig: signal.Signals) -> None:
        logfire.info(f"Received {sig.name}, shutting down worker...")
        shutdown_event.set()
    
    loop = asyncio.get_running_loop()
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler, sig)
    
    logfire.info(
        f"🚀 Starting Order Worker on task queue '{config.task_queue}'",
        task_queue=config.task_queue,
        workflows=[w.__name__ for w in ALL_WORKFLOWS],
        activities=[a.__name__ for a in ALL_ACTIVITIES],
    )
    
    try:
        # Run worker until shutdown
        async with worker:
            await shutdown_event.wait()
    finally:
        logfire.info("👋 Order Worker stopped")


def main() -> None:
    """Entry point for running worker as module."""
    asyncio.run(run_order_worker())


if __name__ == "__main__":
    main()


__all__ = [
    "OrderWorkerConfig",
    "create_order_worker",
    "run_order_worker",
    "ORDER_TASK_QUEUE",
]

"""Temporal Worker Setup — запуск и управление Temporal Workers.

Worker выполняет Workflows и Activities. Один Worker может обрабатывать
несколько Task Queues, но обычно используется один queue на приложение.

Запуск Worker:

    # Как CLI команда
    $ python -m src.Ship.Infrastructure.Temporal.Worker
    
    # Или через entry point (добавить в pyproject.toml)
    $ temporal-worker
    
    # Программно
    from src.Ship.Infrastructure.Temporal.Worker import run_temporal_worker
    await run_temporal_worker()

Регистрация Workflows и Activities:

    # Все workflow и activity классы должны быть зарегистрированы
    # в WorkerConfig или через декораторы
    
    from src.Containers.AppSection.OrderModule.Workflows import CreateOrderWorkflow
    from src.Containers.AppSection.OrderModule.Activities import (
        create_order_activity,
        cancel_order_activity,
    )
    
    config = TemporalWorkerConfig(
        workflows=[CreateOrderWorkflow],
        activities=[create_order_activity, cancel_order_activity],
    )
    
    await run_temporal_worker(config)

Конфигурация:
    
    # .env
    TEMPORAL_TASK_QUEUE=hyper-porto
    TEMPORAL_MAX_CONCURRENT_ACTIVITIES=100
    TEMPORAL_MAX_CONCURRENT_WORKFLOWS=100
"""

import asyncio
import anyio
import signal
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from temporalio.client import Client
from temporalio.worker import Worker, SharedStateManager

from src.Ship.Configs.Settings import Settings, get_settings
from src.Ship.Infrastructure.Temporal.Client import (
    get_temporal_client,
    close_temporal_client,
)


@dataclass
class TemporalWorkerConfig:
    """Configuration for Temporal Worker.
    
    Attributes:
        task_queue: Task queue to poll for work
        workflows: List of workflow classes to register
        activities: List of activity functions to register
        max_concurrent_activities: Max concurrent activity executions
        max_concurrent_workflow_tasks: Max concurrent workflow tasks
        max_cached_workflows: Max workflows to keep in cache
        identity: Worker identity for debugging
        graceful_shutdown_timeout: Timeout for graceful shutdown (seconds)
    
    Example:
        config = TemporalWorkerConfig(
            task_queue="orders",
            workflows=[CreateOrderWorkflow, CancelOrderWorkflow],
            activities=[create_order, charge_payment, cancel_order],
        )
    """
    
    task_queue: str = "hyper-porto"
    workflows: list[type] = field(default_factory=list)
    activities: list[Callable[..., Any]] = field(default_factory=list)
    max_concurrent_activities: int = 100
    max_concurrent_workflow_tasks: int = 100
    max_cached_workflows: int = 1000
    identity: str = "hyper-porto-worker"
    graceful_shutdown_timeout: float = 30.0
    
    @classmethod
    def from_settings(cls, settings: Settings) -> "TemporalWorkerConfig":
        """Create config from application Settings.
        
        Note: Workflows and activities must be added manually.
        
        Args:
            settings: Application Settings instance
            
        Returns:
            TemporalWorkerConfig instance
        """
        return cls(
            task_queue=settings.temporal_task_queue,
            max_concurrent_activities=settings.temporal_max_concurrent_activities,
            max_concurrent_workflow_tasks=settings.temporal_max_concurrent_workflows,
            identity=settings.temporal_identity,
        )
    
    def add_workflow(self, workflow_cls: type) -> "TemporalWorkerConfig":
        """Add a workflow class (fluent API).
        
        Args:
            workflow_cls: Workflow class decorated with @workflow.defn
            
        Returns:
            Self for chaining
        """
        self.workflows.append(workflow_cls)
        return self
    
    def add_activity(self, activity_fn: Callable[..., Any]) -> "TemporalWorkerConfig":
        """Add an activity function (fluent API).
        
        Args:
            activity_fn: Activity function decorated with @activity.defn
            
        Returns:
            Self for chaining
        """
        self.activities.append(activity_fn)
        return self
    
    def add_workflows(self, *workflow_classes: type) -> "TemporalWorkerConfig":
        """Add multiple workflow classes (fluent API).
        
        Args:
            *workflow_classes: Workflow classes
            
        Returns:
            Self for chaining
        """
        self.workflows.extend(workflow_classes)
        return self
    
    def add_activities(self, *activity_fns: Callable[..., Any]) -> "TemporalWorkerConfig":
        """Add multiple activity functions (fluent API).
        
        Args:
            *activity_fns: Activity functions
            
        Returns:
            Self for chaining
        """
        self.activities.extend(activity_fns)
        return self


async def create_temporal_worker(
    client: Client | None = None,
    config: TemporalWorkerConfig | None = None,
) -> Worker:
    """Create a Temporal Worker instance.
    
    Args:
        client: Temporal client (uses singleton if None)
        config: Worker configuration (uses defaults if None)
        
    Returns:
        Configured Worker instance (not started)
        
    Example:
        config = TemporalWorkerConfig(
            workflows=[MyWorkflow],
            activities=[my_activity],
        )
        worker = await create_temporal_worker(config=config)
        
        # Run worker
        async with worker:
            await worker.run()
    """
    if client is None:
        client = await get_temporal_client()
    
    if config is None:
        config = TemporalWorkerConfig.from_settings(get_settings())
    
    worker = Worker(
        client=client,
        task_queue=config.task_queue,
        workflows=config.workflows,
        activities=config.activities,
        max_concurrent_activities=config.max_concurrent_activities,
        max_concurrent_workflow_tasks=config.max_concurrent_workflow_tasks,
        max_cached_workflows=config.max_cached_workflows,
        identity=config.identity,
    )
    
    return worker


async def run_temporal_worker(
    config: TemporalWorkerConfig | None = None,
) -> None:
    """Run Temporal Worker with graceful shutdown.
    
    Blocks until worker is stopped (via signal or error).
    Handles SIGINT/SIGTERM for graceful shutdown.
    
    Args:
        config: Worker configuration
        
    Example:
        # Simple run
        await run_temporal_worker()
        
        # With custom config
        config = TemporalWorkerConfig(
            task_queue="orders",
            workflows=[CreateOrderWorkflow],
            activities=[create_order_activity],
        )
        await run_temporal_worker(config)
    """
    if config is None:
        config = TemporalWorkerConfig.from_settings(get_settings())
    
    # Get or create client
    client = await get_temporal_client()
    
    # Create worker
    worker = await create_temporal_worker(client, config)
    
    # Setup graceful shutdown
    shutdown_event = anyio.Event()
    
    def signal_handler(sig: signal.Signals) -> None:
        print(f"\n🛑 Received {sig.name}, shutting down worker gracefully...")
        shutdown_event.set()
    
    # Register signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler, sig)
    
    print(f"🚀 Starting Temporal Worker")
    print(f"   Task Queue: {config.task_queue}")
    print(f"   Workflows: {len(config.workflows)}")
    print(f"   Activities: {len(config.activities)}")
    print(f"   Max Concurrent Activities: {config.max_concurrent_activities}")
    print(f"   Max Concurrent Workflows: {config.max_concurrent_workflow_tasks}")
    
    try:
        # Run worker until shutdown signal
        async with worker:
            # Wait for shutdown signal
            await shutdown_event.wait()
            
    except Exception as e:
        print(f"❌ Worker error: {e}")
        raise
        
    finally:
        # Cleanup
        await close_temporal_client()
        print("✅ Worker shutdown complete")


def get_all_workflows() -> list[type]:
    """Discover all registered Temporal workflows.
    
    Override this function in your application to return
    all workflow classes that should be registered.
    
    Returns:
        List of workflow classes
        
    Example:
        # In your app's startup
        def get_all_workflows():
            from src.Containers.AppSection.OrderModule.Workflows import (
                CreateOrderWorkflow,
                CancelOrderWorkflow,
            )
            return [CreateOrderWorkflow, CancelOrderWorkflow]
    """
    # Import your workflows here
    # from src.Containers.AppSection.OrderModule.Workflows import ...
    return []


def get_all_activities() -> list[Callable[..., Any]]:
    """Discover all registered Temporal activities.
    
    Override this function in your application to return
    all activity functions that should be registered.
    
    Returns:
        List of activity functions
        
    Example:
        # In your app's startup
        def get_all_activities():
            from src.Containers.AppSection.OrderModule.Activities import (
                create_order_activity,
                cancel_order_activity,
            )
            return [create_order_activity, cancel_order_activity]
    """
    # Import your activities here
    # from src.Containers.AppSection.OrderModule.Activities import ...
    return []


# CLI entry point
if __name__ == "__main__":
    """Run worker from command line.
    
    Usage:
        python -m src.Ship.Infrastructure.Temporal.Worker
    """
    import structlog
    
    structlog.configure(
        processors=[
            structlog.dev.ConsoleRenderer(colors=True),
        ],
    )
    
    # Build config with all registered workflows/activities
    config = TemporalWorkerConfig.from_settings(get_settings())
    config.workflows = get_all_workflows()
    config.activities = get_all_activities()
    
    if not config.workflows and not config.activities:
        print("⚠️  No workflows or activities registered!")
        print("   Override get_all_workflows() and get_all_activities()")
        print("   or pass workflows/activities to TemporalWorkerConfig")
    
    asyncio.run(run_temporal_worker(config))


__all__ = [
    "TemporalWorkerConfig",
    "create_temporal_worker",
    "run_temporal_worker",
    "get_all_workflows",
    "get_all_activities",
]

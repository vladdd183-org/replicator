"""Temporal CLI Commands — команды для управления Temporal worker.

Использование:

    # Запуск worker
    $ python -m src.Ship.CLI.Commands.TemporalCommands worker
    
    # С кастомной task queue
    $ python -m src.Ship.CLI.Commands.TemporalCommands worker --task-queue orders
    
    # Проверка health
    $ python -m src.Ship.CLI.Commands.TemporalCommands health

Интеграция с Litestar CLI:

    # Добавить в pyproject.toml:
    [project.entry-points."litestar.commands"]
    temporal = "src.Ship.CLI.Commands.TemporalCommands:temporal_group"
    
    # Тогда:
    $ litestar temporal worker
"""

import asyncio
import click
import structlog

from src.Ship.Configs.Settings import get_settings
from src.Ship.Infrastructure.Temporal.Client import health_check
from src.Ship.Infrastructure.Temporal.Worker import (
    TemporalWorkerConfig,
    run_temporal_worker,
    get_all_workflows,
    get_all_activities,
)


@click.group(name="temporal")
def temporal_group() -> None:
    """Temporal.io worker management commands."""
    pass


@temporal_group.command(name="worker")
@click.option(
    "--task-queue",
    "-q",
    default=None,
    help="Task queue name (default: from settings)",
)
@click.option(
    "--max-activities",
    "-a",
    default=None,
    type=int,
    help="Max concurrent activities (default: from settings)",
)
@click.option(
    "--max-workflows",
    "-w",
    default=None,
    type=int,
    help="Max concurrent workflows (default: from settings)",
)
def run_worker(
    task_queue: str | None,
    max_activities: int | None,
    max_workflows: int | None,
) -> None:
    """Start Temporal worker.
    
    The worker will poll for tasks from the specified queue
    and execute registered workflows and activities.
    
    Press Ctrl+C for graceful shutdown.
    
    Examples:
    
        # Start with defaults from settings
        $ cli temporal worker
        
        # Custom task queue
        $ cli temporal worker --task-queue orders
        
        # Custom concurrency
        $ cli temporal worker --max-activities 50 --max-workflows 50
    """
    # Configure logging
    structlog.configure(
        processors=[
            structlog.dev.ConsoleRenderer(colors=True),
        ],
    )
    
    settings = get_settings()
    
    # Build config
    config = TemporalWorkerConfig.from_settings(settings)
    
    if task_queue:
        config.task_queue = task_queue
    if max_activities:
        config.max_concurrent_activities = max_activities
    if max_workflows:
        config.max_concurrent_workflow_tasks = max_workflows
    
    # Get registered workflows and activities
    config.workflows = get_all_workflows()
    config.activities = get_all_activities()
    
    if not config.workflows and not config.activities:
        click.echo("⚠️  No workflows or activities registered!")
        click.echo("")
        click.echo("To register workflows and activities, edit:")
        click.echo("  src/Ship/Infrastructure/Temporal/Worker.py")
        click.echo("")
        click.echo("And implement get_all_workflows() and get_all_activities()")
        click.echo("")
        click.echo("Example:")
        click.echo("  def get_all_workflows():")
        click.echo("      from src.Containers.AppSection.OrderModule.Workflows import (")
        click.echo("          CreateOrderWorkflow,")
        click.echo("      )")
        click.echo("      return [CreateOrderWorkflow]")
        click.echo("")
    
    click.echo("=" * 60)
    click.echo("🚀 Starting Temporal Worker")
    click.echo("=" * 60)
    click.echo(f"   Host: {settings.temporal_host}")
    click.echo(f"   Namespace: {settings.temporal_namespace}")
    click.echo(f"   Task Queue: {config.task_queue}")
    click.echo(f"   Workflows: {len(config.workflows)}")
    click.echo(f"   Activities: {len(config.activities)}")
    click.echo(f"   Max Activities: {config.max_concurrent_activities}")
    click.echo(f"   Max Workflows: {config.max_concurrent_workflow_tasks}")
    click.echo("=" * 60)
    click.echo("")
    click.echo("Press Ctrl+C to stop gracefully")
    click.echo("")
    
    # Run worker
    asyncio.run(run_temporal_worker(config))


@temporal_group.command(name="health")
def check_health() -> None:
    """Check Temporal connection health.
    
    Verifies connectivity to Temporal server.
    
    Example:
    
        $ cli temporal health
        ✅ Temporal is healthy
           Host: localhost:7233
           Namespace: default
    """
    async def _check() -> dict:
        return await health_check()
    
    result = asyncio.run(_check())
    
    if result["status"] == "healthy":
        click.echo(f"✅ Temporal is healthy")
        click.echo(f"   Host: {result['host']}")
        click.echo(f"   Namespace: {result['namespace']}")
    else:
        click.echo(f"❌ Temporal is unhealthy")
        click.echo(f"   Host: {result['host']}")
        click.echo(f"   Namespace: {result['namespace']}")
        click.echo(f"   Error: {result.get('error', 'Unknown')}")
        raise SystemExit(1)


@temporal_group.command(name="info")
def show_info() -> None:
    """Show Temporal configuration info.
    
    Displays current Temporal settings without connecting.
    
    Example:
    
        $ cli temporal info
    """
    settings = get_settings()
    
    click.echo("=" * 60)
    click.echo("⚙️  Temporal Configuration")
    click.echo("=" * 60)
    click.echo(f"   Host: {settings.temporal_host}")
    click.echo(f"   Namespace: {settings.temporal_namespace}")
    click.echo(f"   Task Queue: {settings.temporal_task_queue}")
    click.echo(f"   Identity: {settings.temporal_identity}")
    click.echo(f"   Max Concurrent Activities: {settings.temporal_max_concurrent_activities}")
    click.echo(f"   Max Concurrent Workflows: {settings.temporal_max_concurrent_workflows}")
    click.echo(f"   TLS Enabled: {settings.temporal_enable_tls}")
    if settings.temporal_enable_tls:
        click.echo(f"   Client Cert: {settings.temporal_client_cert_path or 'Not set'}")
        click.echo(f"   Client Key: {settings.temporal_client_key_path or 'Not set'}")
    click.echo("=" * 60)


# CLI entry point
if __name__ == "__main__":
    temporal_group()


__all__ = [
    "temporal_group",
    "run_worker",
    "check_health",
    "show_info",
]

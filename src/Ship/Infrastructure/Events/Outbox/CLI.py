"""CLI commands for Outbox management.

Provides commands for:
- Processing outbox events manually
- Viewing outbox statistics
- Cleaning up old events
- Resetting failed events
"""

import asyncio
from uuid import UUID

import click
from rich.console import Console
from rich.table import Table

from src.Ship.CLI.Decorators import with_container, handle_cli_result
from src.Ship.Infrastructure.Events.Outbox.Repository import OutboxEventRepository
from src.Ship.Infrastructure.Events.Outbox.Publisher import OutboxPublisherService


console = Console()


@click.group(name="outbox")
def outbox_cli():
    """Outbox event management commands."""
    pass


@outbox_cli.command(name="stats")
@with_container
async def stats_command():
    """Show outbox statistics."""
    repo = OutboxEventRepository()
    stats = await repo.count_by_status()
    
    table = Table(title="Outbox Statistics")
    table.add_column("Status", style="cyan")
    table.add_column("Count", style="magenta", justify="right")
    
    table.add_row("Total", str(stats["total"]))
    table.add_row("Published", str(stats["published"]))
    table.add_row("Pending", str(stats["pending"]))
    table.add_row("Failed (retrying)", str(stats["failed"]))
    table.add_row("Exhausted", str(stats["exhausted"]))
    
    console.print(table)


@outbox_cli.command(name="process")
@click.option("--limit", "-l", default=100, help="Maximum events to process")
@with_container
async def process_command(limit: int):
    """Process pending outbox events manually."""
    console.print(f"[cyan]Processing up to {limit} outbox events...[/cyan]")
    
    service = OutboxPublisherService()
    result = await service.process_batch(limit=limit)
    
    console.print(f"[green]Processed: {result['processed']}[/green]")
    console.print(f"[green]Published: {result['published']}[/green]")
    if result["failed"] > 0:
        console.print(f"[yellow]Failed: {result['failed']}[/yellow]")


@outbox_cli.command(name="cleanup")
@click.option("--hours", "-h", default=24, help="Delete events older than N hours")
@click.option("--limit", "-l", default=1000, help="Maximum events to delete")
@with_container
async def cleanup_command(hours: int, limit: int):
    """Clean up old published events."""
    console.print(f"[cyan]Cleaning up events older than {hours} hours...[/cyan]")
    
    repo = OutboxEventRepository()
    deleted = await repo.cleanup_published(older_than_hours=hours, limit=limit)
    
    console.print(f"[green]Deleted {deleted} old events[/green]")


@outbox_cli.command(name="failed")
@click.option("--limit", "-l", default=20, help="Maximum events to show")
@click.option("--exhausted", "-e", is_flag=True, help="Include exhausted events")
@with_container
async def failed_command(limit: int, exhausted: bool):
    """Show failed outbox events."""
    repo = OutboxEventRepository()
    events = await repo.get_failed_events(limit=limit, include_exhausted=exhausted)
    
    if not events:
        console.print("[green]No failed events found[/green]")
        return
    
    table = Table(title="Failed Outbox Events")
    table.add_column("ID", style="dim", max_width=8)
    table.add_column("Event Name", style="cyan")
    table.add_column("Retries", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("Error", style="red", max_width=40)
    table.add_column("Created", style="dim")
    
    for event in events:
        table.add_row(
            str(event.id)[:8],
            event.event_name,
            str(event.retry_count),
            str(event.max_retries),
            (event.error_message or "")[:40],
            str(event.created_at)[:19] if event.created_at else "",
        )
    
    console.print(table)


@outbox_cli.command(name="exhausted")
@click.option("--limit", "-l", default=20, help="Maximum events to show")
@with_container
async def exhausted_command(limit: int):
    """Show exhausted (max retries exceeded) events."""
    repo = OutboxEventRepository()
    events = await repo.get_exhausted_events(limit=limit)
    
    if not events:
        console.print("[green]No exhausted events found[/green]")
        return
    
    table = Table(title="Exhausted Outbox Events (require manual intervention)")
    table.add_column("ID", style="dim")
    table.add_column("Event Name", style="cyan")
    table.add_column("Retries", justify="right")
    table.add_column("Error", style="red", max_width=50)
    table.add_column("Created", style="dim")
    
    for event in events:
        table.add_row(
            str(event.id),
            event.event_name,
            str(event.retry_count),
            (event.error_message or "")[:50],
            str(event.created_at)[:19] if event.created_at else "",
        )
    
    console.print(table)


@outbox_cli.command(name="reset")
@click.argument("event_id")
@with_container
async def reset_command(event_id: str):
    """Reset an exhausted event for reprocessing."""
    try:
        event_uuid = UUID(event_id)
    except ValueError:
        console.print(f"[red]Invalid UUID: {event_id}[/red]")
        return
    
    repo = OutboxEventRepository()
    event = await repo.get(event_uuid)
    
    if event is None:
        console.print(f"[red]Event not found: {event_id}[/red]")
        return
    
    if event.is_published:
        console.print(f"[yellow]Event already published: {event_id}[/yellow]")
        return
    
    await repo.reset_exhausted(event_uuid)
    console.print(f"[green]Event reset for reprocessing: {event_id}[/green]")


@outbox_cli.command(name="publish")
@click.argument("event_id")
@with_container
async def publish_command(event_id: str):
    """Force publish a single event."""
    try:
        event_uuid = UUID(event_id)
    except ValueError:
        console.print(f"[red]Invalid UUID: {event_id}[/red]")
        return
    
    repo = OutboxEventRepository()
    event = await repo.get(event_uuid)
    
    if event is None:
        console.print(f"[red]Event not found: {event_id}[/red]")
        return
    
    if event.is_published:
        console.print(f"[yellow]Event already published: {event_id}[/yellow]")
        return
    
    service = OutboxPublisherService(repository=repo)
    success = await service._publish_single_event(event)
    
    if success:
        console.print(f"[green]Event published successfully: {event_id}[/green]")
    else:
        console.print(f"[red]Failed to publish event: {event_id}[/red]")


@outbox_cli.command(name="pending")
@click.option("--limit", "-l", default=20, help="Maximum events to show")
@with_container
async def pending_command(limit: int):
    """Show pending (not yet published) events."""
    repo = OutboxEventRepository()
    events = await repo.get_unpublished(limit=limit, include_retry_ready=True)
    
    if not events:
        console.print("[green]No pending events found[/green]")
        return
    
    table = Table(title="Pending Outbox Events")
    table.add_column("ID", style="dim", max_width=8)
    table.add_column("Event Name", style="cyan")
    table.add_column("Aggregate", style="blue")
    table.add_column("Retries", justify="right")
    table.add_column("Created", style="dim")
    table.add_column("Next Retry", style="dim")
    
    for event in events:
        aggregate = f"{event.aggregate_type}:{event.aggregate_id}" if event.aggregate_type else "-"
        next_retry = str(event.next_retry_at)[:19] if event.next_retry_at else "-"
        
        table.add_row(
            str(event.id)[:8],
            event.event_name,
            aggregate[:20],
            str(event.retry_count),
            str(event.created_at)[:19] if event.created_at else "",
            next_retry,
        )
    
    console.print(table)

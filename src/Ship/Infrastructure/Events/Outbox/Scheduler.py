"""TaskIQ Scheduler configuration for Outbox workers.

Configures scheduled tasks for:
1. Processing outbox events (every minute)
2. Cleaning up old published events (daily)

Usage:
    # Start the scheduler
    taskiq scheduler src.Ship.Infrastructure.Events.Outbox.Scheduler:scheduler
    
    # Or start broker with scheduler
    taskiq worker src.Ship.Infrastructure.Workers.Broker:broker --scheduler src.Ship.Infrastructure.Events.Outbox.Scheduler:scheduler
"""

from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

from src.Ship.Infrastructure.Workers.Broker import broker
from src.Ship.Configs import get_settings


# Get scheduler settings
settings = get_settings()

# Create scheduler with label-based schedule source
# Tasks define their schedules via labels in Publisher.py
scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)


# Define schedule configurations as labels on tasks
# These are applied when tasks are defined in Publisher.py

# Example cron patterns:
# "* * * * *"     - Every minute
# "*/5 * * * *"   - Every 5 minutes
# "0 * * * *"     - Every hour
# "0 0 * * *"     - Daily at midnight
# "0 0 * * 0"     - Weekly on Sunday

# Schedule for outbox event processing
OUTBOX_PROCESS_SCHEDULE = f"*/{settings.outbox_poll_interval_seconds // 60 or 1} * * * *"

# Schedule for outbox cleanup (daily at 3 AM)
OUTBOX_CLEANUP_SCHEDULE = "0 3 * * *"


def get_outbox_schedules() -> dict[str, str]:
    """Get outbox task schedules.
    
    Returns dict mapping task names to cron expressions.
    Useful for documentation and monitoring.
    """
    return {
        "publish_outbox_events": OUTBOX_PROCESS_SCHEDULE,
        "cleanup_outbox_events": OUTBOX_CLEANUP_SCHEDULE,
    }

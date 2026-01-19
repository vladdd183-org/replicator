"""Transactional Outbox Pattern Implementation.

The Transactional Outbox pattern ensures reliable event delivery by:
1. Storing events in the same transaction as business data
2. Processing events asynchronously via background worker
3. Guaranteeing at-least-once delivery with retry logic

Components:
- OutboxEvent: Piccolo model for storing events
- OutboxEventRepository: Data access for outbox events
- OutboxPublisherService: Service for processing outbox events
- OutboxUnitOfWorkMixin: UoW mixin for outbox integration
- CLI commands: Management commands via `python -m src.Ship.CLI.Main outbox`

Usage:
    # BaseUnitOfWork automatically uses outbox when OUTBOX_ENABLED=true
    @dataclass
    class UserUnitOfWork(BaseUnitOfWork):
        users: UserRepository
        
    # Events are automatically saved to outbox on commit
    async with self.uow:
        await self.uow.users.add(user)
        self.uow.set_aggregate_info("User", str(user.id))  # Optional tracking
        self.uow.add_event(UserCreated(user_id=user.id))
        await self.uow.commit()  # Event saved to outbox table

Configuration (Settings):
    OUTBOX_ENABLED=true              # Enable/disable outbox (default: true)
    OUTBOX_BATCH_SIZE=100            # Events per worker run
    OUTBOX_MAX_RETRIES=5             # Max retry attempts
    OUTBOX_BACKOFF_BASE_SECONDS=30   # Exponential backoff base
    OUTBOX_CLEANUP_HOURS=24          # Delete published events after
    OUTBOX_POLL_INTERVAL_SECONDS=60  # Worker poll interval

TaskIQ Tasks:
    - publish_outbox_events(): Process pending events
    - cleanup_outbox_events(): Delete old published events
    - get_outbox_stats(): Get statistics for monitoring
    - reset_exhausted_event(id): Reset failed event for retry
    - publish_single_event(id): Force publish specific event

CLI Commands:
    - outbox stats: Show outbox statistics
    - outbox process: Manually process pending events
    - outbox cleanup: Delete old published events
    - outbox failed: Show failed events
    - outbox exhausted: Show events that exceeded max retries
    - outbox reset <id>: Reset an exhausted event
    - outbox publish <id>: Force publish a single event
    - outbox pending: Show pending events

Import Examples:
    from src.Ship.Infrastructure.Events.Outbox import OutboxEvent
    from src.Ship.Infrastructure.Events.Outbox import OutboxEventRepository
    from src.Ship.Infrastructure.Events.Outbox.Publisher import OutboxPublisherService
    from src.Ship.Infrastructure.Events.Outbox.Providers import OutboxModuleProvider
"""

# Core components - safe to import at module level
from src.Ship.Infrastructure.Events.Outbox.Models import OutboxEvent
from src.Ship.Infrastructure.Events.Outbox.Repository import OutboxEventRepository

# NOTE: Publisher, UnitOfWork, and Providers are imported lazily to avoid
# circular import issues with TaskIQ broker and Settings.
# Import them directly from their modules when needed:
#   from src.Ship.Infrastructure.Events.Outbox.Publisher import OutboxPublisherService
#   from src.Ship.Infrastructure.Events.Outbox.UnitOfWork import OutboxUnitOfWorkMixin
#   from src.Ship.Infrastructure.Events.Outbox.Providers import OutboxModuleProvider

__all__ = [
    # Model
    "OutboxEvent",
    # Repository
    "OutboxEventRepository",
]


def __getattr__(name: str):
    """Lazy import for components that may cause circular imports."""
    if name == "OutboxPublisherService":
        from src.Ship.Infrastructure.Events.Outbox.Publisher import OutboxPublisherService
        return OutboxPublisherService
    if name == "publish_outbox_events":
        from src.Ship.Infrastructure.Events.Outbox.Publisher import publish_outbox_events
        return publish_outbox_events
    if name == "cleanup_outbox_events":
        from src.Ship.Infrastructure.Events.Outbox.Publisher import cleanup_outbox_events
        return cleanup_outbox_events
    if name == "get_outbox_stats":
        from src.Ship.Infrastructure.Events.Outbox.Publisher import get_outbox_stats
        return get_outbox_stats
    if name == "reset_exhausted_event":
        from src.Ship.Infrastructure.Events.Outbox.Publisher import reset_exhausted_event
        return reset_exhausted_event
    if name == "publish_single_event":
        from src.Ship.Infrastructure.Events.Outbox.Publisher import publish_single_event
        return publish_single_event
    if name == "OutboxUnitOfWorkMixin":
        from src.Ship.Infrastructure.Events.Outbox.UnitOfWork import OutboxUnitOfWorkMixin
        return OutboxUnitOfWorkMixin
    if name == "OutboxAwareUnitOfWork":
        from src.Ship.Infrastructure.Events.Outbox.UnitOfWork import OutboxAwareUnitOfWork
        return OutboxAwareUnitOfWork
    if name == "OutboxModuleProvider":
        from src.Ship.Infrastructure.Events.Outbox.Providers import OutboxModuleProvider
        return OutboxModuleProvider
    if name == "OutboxRequestProvider":
        from src.Ship.Infrastructure.Events.Outbox.Providers import OutboxRequestProvider
        return OutboxRequestProvider
    if name == "OutboxCLIProvider":
        from src.Ship.Infrastructure.Events.Outbox.Providers import OutboxCLIProvider
        return OutboxCLIProvider
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

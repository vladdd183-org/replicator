"""Outbox-enabled Unit of Work mixin.

Provides integration between UnitOfWork and Transactional Outbox pattern.
Events are stored in the outbox table instead of being emitted directly,
ensuring reliable delivery even if the application crashes after commit.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from src.Ship.Configs import get_settings
from src.Ship.Infrastructure.Events.Outbox.Repository import OutboxEventRepository

if TYPE_CHECKING:
    from src.Ship.Parents.Event import DomainEvent


@dataclass
class OutboxUnitOfWorkMixin:
    """Mixin for UnitOfWork to support Transactional Outbox pattern.
    
    This mixin modifies how events are handled during commit:
    - If outbox is enabled: Events are saved to outbox table (same transaction)
    - If outbox is disabled: Events are emitted directly after commit (fire-and-forget)
    
    The mixin automatically detects settings and chooses the appropriate strategy.
    
    Usage:
        @dataclass
        class UserUnitOfWork(OutboxUnitOfWorkMixin, BaseUnitOfWork):
            users: UserRepository = field(default_factory=UserRepository)
            
        # Events are automatically routed through outbox
        async with uow:
            await uow.users.add(user)
            uow.add_event(UserCreated(user_id=user.id))
            await uow.commit()  # Event saved to outbox
    
    Configuration:
        Set OUTBOX_ENABLED=true in environment or settings to enable.
        
    Notes:
        - Must be listed BEFORE BaseUnitOfWork in inheritance
        - Requires OutboxEventRepository to be available
        - Background worker must be running to process outbox events
    """
    
    # Outbox repository (injected or created)
    _outbox_repo: OutboxEventRepository | None = field(default=None, repr=False)
    
    # Optional aggregate info for tracing
    _aggregate_type: str | None = field(default=None, repr=False)
    _aggregate_id: str | None = field(default=None, repr=False)
    
    def _get_outbox_repo(self) -> OutboxEventRepository:
        """Get or create outbox repository.
        
        Lazily creates repository if not injected.
        """
        if self._outbox_repo is None:
            self._outbox_repo = OutboxEventRepository()
        return self._outbox_repo
    
    def _is_outbox_enabled(self) -> bool:
        """Check if outbox pattern is enabled.
        
        Returns True if:
        - OUTBOX_ENABLED setting is True
        - Environment allows outbox (not disabled for testing)
        """
        settings = get_settings()
        return getattr(settings, "outbox_enabled", False)
    
    def set_aggregate_info(
        self,
        aggregate_type: str,
        aggregate_id: str | None = None,
    ) -> None:
        """Set aggregate information for event tracing.
        
        When set, all events added via add_event() will be tagged
        with this aggregate info in the outbox table.
        
        Args:
            aggregate_type: Type name of the aggregate (e.g., 'User')
            aggregate_id: ID of the aggregate (optional)
            
        Example:
            async with uow:
                uow.set_aggregate_info("User", str(user.id))
                uow.add_event(UserCreated(...))
                uow.add_event(UserEmailVerified(...))  # Both tagged with User
        """
        self._aggregate_type = aggregate_type
        self._aggregate_id = str(aggregate_id) if aggregate_id else None
    
    async def _save_events_to_outbox(self) -> None:
        """Save pending events to outbox table.
        
        Called during transaction commit when outbox is enabled.
        Events are saved within the same transaction as business data.
        """
        if not hasattr(self, "_events") or not self._events:
            return
        
        repo = self._get_outbox_repo()
        
        for event in self._events:
            await repo.add_from_domain_event(
                event=event,
                aggregate_type=self._aggregate_type,
                aggregate_id=self._aggregate_id,
            )


@dataclass
class OutboxAwareUnitOfWork:
    """Complete UnitOfWork with built-in outbox support.
    
    This is a standalone UnitOfWork implementation that includes
    outbox support without requiring multiple inheritance.
    
    Use this as a base class for your UoW if you want automatic
    outbox integration based on settings.
    
    Features:
    - Automatic outbox/direct emit based on settings
    - Aggregate info tracking for event correlation
    - Fallback to direct emit when outbox is disabled
    - Compatible with existing Litestar event listeners
    
    Example:
        @dataclass
        class OrderUnitOfWork(OutboxAwareUnitOfWork):
            orders: OrderRepository = field(default_factory=OrderRepository)
            
        # In action:
        async with uow:
            order = Order(...)
            await uow.orders.add(order)
            uow.set_aggregate_info("Order", str(order.id))
            uow.add_event(OrderCreated(order_id=order.id))
            await uow.commit()
    """
    
    from dataclasses import field as dataclass_field
    from typing import Callable
    
    # Event emitter (from Litestar)
    _emit: Any = field(default=None, repr=False)
    
    # Litestar app instance
    _app: Any = field(default=None, repr=False)
    
    # Outbox repository
    _outbox_repo: OutboxEventRepository | None = field(default=None, repr=False)
    
    # Aggregate tracking
    _aggregate_type: str | None = field(default=None, repr=False)
    _aggregate_id: str | None = field(default=None, repr=False)
    
    # Internal state
    _events: list = field(default_factory=list, init=False, repr=False)
    _committed: bool = field(default=False, init=False, repr=False)
    _transaction: Any = field(default=None, init=False, repr=False)
    
    def _get_engine(self):
        """Get database engine."""
        from piccolo.engine import engine_finder
        engine = engine_finder()
        if engine is None:
            raise RuntimeError("No Piccolo engine configured")
        return engine
    
    def _get_outbox_repo(self) -> OutboxEventRepository:
        """Get or create outbox repository."""
        if self._outbox_repo is None:
            self._outbox_repo = OutboxEventRepository()
        return self._outbox_repo
    
    def _is_outbox_enabled(self) -> bool:
        """Check if outbox is enabled."""
        settings = get_settings()
        return getattr(settings, "outbox_enabled", False)
    
    def set_aggregate_info(
        self,
        aggregate_type: str,
        aggregate_id: str | None = None,
    ) -> None:
        """Set aggregate info for event tracing."""
        self._aggregate_type = aggregate_type
        self._aggregate_id = str(aggregate_id) if aggregate_id else None
    
    def add_event(self, event: "DomainEvent") -> None:
        """Add event for publishing after commit."""
        self._events.append(event)
    
    @property
    def events(self) -> list:
        """Get pending events."""
        return self._events.copy()
    
    async def __aenter__(self):
        """Enter transaction context."""
        self._committed = False
        engine = self._get_engine()
        self._transaction = engine.transaction()
        await self._transaction.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit transaction context with outbox support."""
        
        if self._transaction is None:
            self._events.clear()
            self._committed = False
            return
        
        transaction = self._transaction
        self._transaction = None
        
        try:
            # Exception during transaction -> rollback
            if exc_type is not None:
                await transaction.__aexit__(exc_type, exc_val, exc_tb)
                self._events.clear()
                self._committed = False
                return
            
            # No commit called -> rollback
            if not self._committed:
                await transaction.__aexit__(
                    RuntimeError,
                    RuntimeError("UnitOfWork exited without commit()"),
                    None,
                )
                self._events.clear()
                return
            
            # Save events to outbox (if enabled) BEFORE commit
            if self._is_outbox_enabled() and self._events:
                await self._save_events_to_outbox()
            
            # Commit transaction
            await transaction.__aexit__(None, None, None)
            
            # If outbox disabled, emit events directly (fire-and-forget)
            if not self._is_outbox_enabled() and self._events:
                await self._emit_events_directly()
            
            self._events.clear()
            
        finally:
            self._committed = False
            self._aggregate_type = None
            self._aggregate_id = None
    
    async def _save_events_to_outbox(self) -> None:
        """Save events to outbox table."""
        repo = self._get_outbox_repo()
        for event in self._events:
            await repo.add_from_domain_event(
                event=event,
                aggregate_type=self._aggregate_type,
                aggregate_id=self._aggregate_id,
            )
    
    async def _emit_events_directly(self) -> None:
        """Emit events directly via Litestar."""
        import logfire
        
        if self._emit is not None:
            for event in self._events:
                self._emit(
                    event.event_name,
                    app=self._app,
                    **event.model_dump(mode="json"),
                )
        else:
            for event in self._events:
                logfire.info(
                    f"📤 Event (no emitter): {event.event_name}",
                    event_name=event.event_name,
                    event_data=event.model_dump(mode="json"),
                )
    
    async def commit(self) -> None:
        """Mark transaction ready for commit."""
        if self._transaction is None:
            raise RuntimeError("commit() must be inside 'async with'")
        self._committed = True
    
    async def rollback(self) -> None:
        """Rollback transaction."""
        self._events.clear()
        self._committed = False
        if self._transaction is not None:
            transaction = self._transaction
            self._transaction = None
            await transaction.__aexit__(Exception, Exception("rollback"), None)

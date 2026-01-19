"""Base Unit of Work class according to Hyper-Porto architecture.

UnitOfWork manages transactions and domain event publishing.
Supports two modes:
1. Direct emit (fire-and-forget) - events emitted after commit
2. Transactional Outbox - events saved to outbox table for reliable delivery

Mode is controlled by OUTBOX_ENABLED setting.

Note: For Piccolo ORM, transactions are managed via engine.transaction() context manager.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Self

from piccolo.engine import engine_finder

if TYPE_CHECKING:
    from piccolo.engine.sqlite import SQLiteEngine
    from piccolo.engine.postgres import PostgresEngine
    from litestar import Litestar
    from src.Ship.Parents.Event import DomainEvent
    from src.Ship.Infrastructure.Events.Outbox.Repository import OutboxEventRepository

# Type alias for event emitter function
EventEmitterFunc = Callable[[str, Any], None] | None


@dataclass
class BaseUnitOfWork:
    """Base Unit of Work class with Transactional Outbox support.
    
    UnitOfWork manages transactions and ensures consistency.
    Inheritors only add repositories.
    
    Event Delivery Modes:
    1. Outbox Pattern (OUTBOX_ENABLED=true, default):
       - Events are saved to outbox_events table within the transaction
       - Background worker processes and publishes events
       - Guarantees at-least-once delivery
       
    2. Direct Emit (OUTBOX_ENABLED=false):
       - Events are emitted fire-and-forget after commit
       - Events may be lost if app crashes after commit
       - Faster, but less reliable
    
    Aggregate Tracking:
    Use set_aggregate_info() to tag events with aggregate info.
    This enables filtering and debugging in the outbox table.
    
    Example:
        @dataclass
        class UserUnitOfWork(BaseUnitOfWork):
            users: UserRepository = field(default_factory=UserRepository)
            
        # Usage in Action:
        async with self.uow:
            user = User(email=data.email, ...)
            await self.uow.users.add(user)
            self.uow.set_aggregate_info("User", str(user.id))
            self.uow.add_event(UserCreated(user_id=user.id))
            await self.uow.commit()
    """
    
    # Event emitter function from Litestar (injected via DI)
    # This is the app.emit function that publishes events to listeners
    _emit: EventEmitterFunc = field(default=None, repr=False)
    
    # Litestar app instance for passing to event listeners
    _app: "Litestar | None" = field(default=None, repr=False)
    
    # Outbox repository (lazily created if needed)
    _outbox_repo: "OutboxEventRepository | None" = field(default=None, repr=False)
    
    # Aggregate tracking for outbox events
    _aggregate_type: str | None = field(default=None, init=False, repr=False)
    _aggregate_id: str | None = field(default=None, init=False, repr=False)
    
    # Internal state
    _events: list["DomainEvent"] = field(default_factory=list, init=False, repr=False)
    _committed: bool = field(default=False, init=False, repr=False)
    _transaction: object | None = field(default=None, init=False, repr=False)
    
    def _get_engine(self) -> "SQLiteEngine | PostgresEngine":
        """Get database engine from Piccolo configuration.
        
        Returns:
            Configured Piccolo engine
        """
        engine = engine_finder()
        if engine is None:
            raise RuntimeError("No Piccolo engine configured. Check piccolo_conf.py")
        return engine
    
    def _is_outbox_enabled(self) -> bool:
        """Check if Transactional Outbox pattern is enabled.
        
        Reads from settings. Can be overridden in subclasses.
        
        Returns:
            True if outbox is enabled
        """
        from src.Ship.Configs import get_settings
        settings = get_settings()
        return getattr(settings, "outbox_enabled", False)
    
    def _get_outbox_repo(self) -> "OutboxEventRepository":
        """Get or create outbox repository.
        
        Lazily creates repository if not injected.
        
        Returns:
            OutboxEventRepository instance
        """
        if self._outbox_repo is None:
            from src.Ship.Infrastructure.Events.Outbox.Repository import OutboxEventRepository
            self._outbox_repo = OutboxEventRepository()
        return self._outbox_repo
    
    def set_aggregate_info(
        self,
        aggregate_type: str,
        aggregate_id: str | None = None,
    ) -> None:
        """Set aggregate information for outbox event tracking.
        
        When outbox is enabled, events will be tagged with this info,
        enabling filtering and debugging by aggregate.
        
        Args:
            aggregate_type: Type name of the aggregate (e.g., 'User', 'Order')
            aggregate_id: ID of the aggregate instance
            
        Example:
            async with uow:
                uow.set_aggregate_info("User", str(user.id))
                uow.add_event(UserCreated(user_id=user.id))
                uow.add_event(WelcomeEmailQueued(user_id=user.id))
                await uow.commit()
        """
        self._aggregate_type = aggregate_type
        self._aggregate_id = str(aggregate_id) if aggregate_id else None
    
    async def _save_events_to_outbox(self) -> None:
        """Save pending events to outbox table.
        
        Called during commit when outbox is enabled.
        Events are saved within the same database transaction.
        """
        if not self._events:
            return
        
        repo = self._get_outbox_repo()
        
        for event in self._events:
            await repo.add_from_domain_event(
                event=event,
                aggregate_type=self._aggregate_type,
                aggregate_id=self._aggregate_id,
            )
    
    async def _emit_events_directly(self) -> None:
        """Emit events directly via Litestar (fire-and-forget).
        
        Called after commit when outbox is disabled.
        Events may be lost if app crashes after commit.
        """
        import logfire
        
        if self._emit is not None:
            for event in self._events:
                # Emit event with app instance and all event data as kwargs
                self._emit(event.event_name, app=self._app, **event.model_dump(mode="json"))
        else:
            # Log events when no emitter is available (CLI, tests, etc.)
            for event in self._events:
                logfire.info(
                    f"📤 Event (no emitter): {event.event_name}",
                    event_name=event.event_name,
                    event_data=event.model_dump(mode="json"),
                )
    
    async def __aenter__(self: Self) -> Self:
        """Enter transaction context.
        
        Starts a database transaction using Piccolo engine.
        """
        self._committed = False
        engine = self._get_engine()
        self._transaction = engine.transaction()
        await self._transaction.__aenter__()
        return self
    
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit transaction context with Transactional Outbox support.
        
        Design contract:
        - DB commit happens only if `commit()` was called and no exception occurred.
        - If `commit()` wasn't called, we rollback even if there was no exception.
        - Event delivery depends on OUTBOX_ENABLED setting:
          - Outbox enabled: Events saved to outbox table BEFORE commit (same transaction)
          - Outbox disabled: Events emitted fire-and-forget AFTER commit
        """
        if self._transaction is None:
            # Nothing to finalize. Ensure clean state.
            self._events.clear()
            self._committed = False
            self._aggregate_type = None
            self._aggregate_id = None
            return

        transaction = self._transaction
        self._transaction = None  # Prevent double-finalization (idempotency)

        try:
            # 1) If an exception happened inside the transaction block -> rollback.
            if exc_type is not None:
                await transaction.__aexit__(exc_type, exc_val, exc_tb)
                self._events.clear()
                self._committed = False
                return

            # 2) If commit() wasn't called -> rollback by forcing an exception path.
            if not self._committed:
                await transaction.__aexit__(
                    RuntimeError,
                    RuntimeError("UnitOfWork exited without calling commit()"),
                    None,
                )
                self._events.clear()
                return

            # 3) If outbox is enabled, save events to outbox table BEFORE commit
            #    This ensures events are in the same transaction as business data
            use_outbox = self._is_outbox_enabled()
            if use_outbox and self._events:
                await self._save_events_to_outbox()

            # 4) Commit DB transaction
            await transaction.__aexit__(None, None, None)

            # 5) If outbox is DISABLED, emit events directly (fire-and-forget)
            #    This is the legacy behavior for backward compatibility
            if not use_outbox and self._events:
                await self._emit_events_directly()

            self._events.clear()
        finally:
            # Reset state so the same UoW instance can't accidentally be reused.
            self._committed = False
            self._aggregate_type = None
            self._aggregate_id = None
    
    def add_event(self, event: "DomainEvent") -> None:
        """Add domain event for publishing after commit.
        
        Args:
            event: Domain event to publish
        """
        self._events.append(event)
    
    async def commit(self) -> None:
        """Mark current transaction as ready to commit.
        
        Important:
        - Actual DB commit happens when leaving the `async with uow:` block.
        - Domain events are emitted strictly AFTER successful DB commit, also on exit.
        - If commit() wasn't called, the transaction is rolled back on exit.
        """
        if self._transaction is None:
            raise RuntimeError("commit() must be called inside 'async with uow:' block")

        self._committed = True
    
    async def rollback(self) -> None:
        """Rollback transaction and clear events.
        
        Note: Piccolo transaction rollback is handled by __aexit__ on exception.
        This method clears events and resets state.
        """
        self._events.clear()
        self._committed = False
        self._aggregate_type = None
        self._aggregate_id = None

        if self._transaction is not None:
            transaction = self._transaction
            self._transaction = None
            await transaction.__aexit__(Exception, Exception("rollback"), None)
    
    @property
    def events(self) -> list["DomainEvent"]:
        """Get pending events.
        
        Returns:
            List of pending domain events
        """
        return self._events.copy()
    
    async def execute_with_event(
        self: Self,
        operation: Coroutine[Any, Any, Any],
        event: "DomainEvent",
    ) -> None:
        """Execute operation within transaction and publish event after commit.
        
        Reduces boilerplate for common pattern:
            async with self.uow:
                await operation
                self.uow.add_event(event)
                await self.uow.commit()
        
        Args:
            operation: Async operation to execute (awaitable)
            event: Domain event to publish after commit
            
        Example:
            await self.uow.execute_with_event(
                self.uow.users.add(user),
                UserCreated(user_id=user.id, email=user.email),
            )
        """
        async with self:
            await operation
            self.add_event(event)
            await self.commit()

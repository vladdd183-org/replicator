"""Base Unit of Work class according to Hyper-Porto architecture.

UnitOfWork manages transactions and domain event publishing.
Integrates with litestar.events for event dispatching after commit.

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

# Type alias for event emitter function
EventEmitterFunc = Callable[[str, Any], None] | None


@dataclass
class BaseUnitOfWork:
    """Base Unit of Work class.
    
    UnitOfWork manages transactions and ensures consistency.
    Inheritors only add repositories.
    
    Integration with litestar.events:
    Events are published AFTER successful commit via emit() function.
    
    For Piccolo ORM:
    Uses engine.transaction() for transaction management.
    
    Example:
        @dataclass
        class UserUnitOfWork(BaseUnitOfWork):
            users: UserRepository = field(default_factory=UserRepository)
            
        # Usage in Action:
        async with self.uow:
            user = User(email=data.email, ...)
            await self.uow.users.add(user)
            self.uow.add_event(UserCreated(user_id=user.id))
            await self.uow.commit()
    """
    
    # Event emitter function from Litestar (injected via DI)
    # This is the app.emit function that publishes events to listeners
    _emit: EventEmitterFunc = field(default=None, repr=False)
    
    # Litestar app instance for passing to event listeners
    _app: "Litestar | None" = field(default=None, repr=False)
    
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
        """Exit transaction context.
        
        Design contract:
        - DB commit happens only if `commit()` was called and no exception occurred.
        - If `commit()` wasn't called, we rollback even if there was no exception.
        - Domain events are emitted strictly AFTER successful transaction commit.
        """
        if self._transaction is None:
            # Nothing to finalize. Ensure clean state.
            self._events.clear()
            self._committed = False
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

            # 3) Commit DB transaction first.
            await transaction.__aexit__(None, None, None)

            # 4) Only after successful commit emit all collected domain events.
            if self._emit is not None:
                for event in self._events:
                    # Emit event with app instance and all event data as kwargs
                    # app is required for listeners to access ChannelsPlugin
                    self._emit(event.event_name, app=self._app, **event.model_dump(mode="json"))
            else:
                # Log events when no emitter is available (CLI, tests, etc.)
                import logfire

                for event in self._events:
                    logfire.info(
                        f"📤 Event (no emitter): {event.event_name}",
                        event_name=event.event_name,
                        event_data=event.model_dump(mode="json"),
                    )

            self._events.clear()
        finally:
            # Reset state so the same UoW instance can't accidentally be reused.
            self._committed = False
    
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

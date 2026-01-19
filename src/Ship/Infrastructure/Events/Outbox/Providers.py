"""Dependency injection providers for Outbox module.

Provides OutboxEventRepository for injection via Dishka.

Note: OutboxPublisherService is NOT provided via DI because it causes
circular import issues with the TaskIQ broker. Instead, create it
directly in actions/workers when needed:

    from src.Ship.Infrastructure.Events.Outbox.Publisher import OutboxPublisherService
    
    service = OutboxPublisherService(repository=repo, app=request.app)
"""

from dishka import Provider, Scope, provide

from src.Ship.Infrastructure.Events.Outbox.Repository import OutboxEventRepository


class OutboxModuleProvider(Provider):
    """Core provider for Outbox module - APP scope.
    
    Provides stateless/singleton dependencies.
    Only provides OutboxEventRepository to avoid circular imports.
    """
    
    scope = Scope.APP
    
    # Repository is stateless, can be singleton
    outbox_repository = provide(OutboxEventRepository)


class OutboxRequestProvider(Provider):
    """Request-scoped provider for Outbox module.
    
    Note: OutboxPublisherService is not provided here due to
    circular import issues. Create it manually when needed.
    """
    
    scope = Scope.REQUEST


class OutboxCLIProvider(Provider):
    """CLI/Worker-scoped provider for Outbox module.
    
    Note: OutboxPublisherService is not provided here due to
    circular import issues. Create it manually when needed.
    """
    
    scope = Scope.REQUEST

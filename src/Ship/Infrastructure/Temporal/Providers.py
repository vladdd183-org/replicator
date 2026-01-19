"""Temporal DI Providers — Dishka providers для Temporal.

Предоставляет:
- TemporalClientProvider: Client для запуска workflows
- TemporalWorkerProvider: Worker configuration

Регистрация:
    # В AppProvider или get_all_providers()
    from src.Ship.Infrastructure.Temporal.Providers import (
        TemporalModuleProvider,
    )
    
    def get_all_providers():
        return [
            ...
            TemporalModuleProvider(),
        ]

Использование в Controller/Action:
    from temporalio.client import Client
    from dishka.integrations.litestar import FromDishka
    
    @post("/orders")
    async def create_order(
        data: CreateOrderRequest,
        client: FromDishka[Client],  # Temporal Client
    ) -> Response:
        handle = await client.start_workflow(
            CreateOrderWorkflow.run,
            data,
            id=f"order-{data.order_id}",
            task_queue="hyper-porto",
        )
        ...
"""

from temporalio.client import Client

from dishka import Provider, Scope, provide

from src.Ship.Configs.Settings import Settings
from src.Ship.Infrastructure.Temporal.Client import (
    TemporalClientConfig,
    create_temporal_client,
)
from src.Ship.Infrastructure.Temporal.Worker import (
    TemporalWorkerConfig,
)


class TemporalModuleProvider(Provider):
    """Temporal module provider for Dishka DI.
    
    Provides:
    - TemporalClientConfig: Configuration for client
    - TemporalWorkerConfig: Configuration for worker
    - Client: Temporal Client (APP scope - singleton)
    
    Example:
        # In get_all_providers()
        return [
            ...
            TemporalModuleProvider(),
        ]
    """
    
    scope = Scope.APP
    
    @provide
    def provide_client_config(self, settings: Settings) -> TemporalClientConfig:
        """Provide Temporal Client configuration from Settings."""
        return TemporalClientConfig.from_settings(settings)
    
    @provide
    def provide_worker_config(self, settings: Settings) -> TemporalWorkerConfig:
        """Provide Temporal Worker configuration from Settings."""
        return TemporalWorkerConfig.from_settings(settings)
    
    @provide
    async def provide_client(self, config: TemporalClientConfig) -> Client:
        """Provide Temporal Client (singleton).
        
        Creates a new connection to Temporal server.
        The client is shared across all requests.
        
        Returns:
            Connected Temporal Client
        """
        return await create_temporal_client(config)


class TemporalRequestProvider(Provider):
    """Temporal request-scoped provider.
    
    Currently empty, but can be extended for request-specific
    Temporal dependencies (e.g., workflow handles, execution contexts).
    
    Example:
        # If you need request-specific Temporal state
        class TemporalRequestProvider(Provider):
            scope = Scope.REQUEST
            
            @provide
            def provide_execution_context(
                self, 
                client: Client,
                request: Request,
            ) -> WorkflowExecutionContext:
                ...
    """
    
    scope = Scope.REQUEST


# Export all
__all__ = [
    "TemporalModuleProvider",
    "TemporalRequestProvider",
]

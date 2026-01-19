"""Order module dependency injection providers.

Consolidated providers with clear scope separation.
Dishka automatically resolves dependencies by type hints.

Architecture:
- OrderModuleProvider: APP scope - Temporal Client, stateless tasks
- _BaseOrderRequestProvider: Base class with common REQUEST scope dependencies
- OrderRequestProvider: HTTP context (inherits base + adds UoW with emit)
- OrderCLIProvider: CLI context (inherits base + adds UoW without emit)

Temporal Integration:
- Temporal Client is APP scope (singleton connection)
- Workflow Actions are REQUEST scope (use client + UoW)
"""

from dishka import Provider, Scope, provide
from litestar import Request
from temporalio.client import Client as TemporalClient

from src.Containers.AppSection.OrderModule.Actions.CreateOrderAction import CreateOrderAction
from src.Containers.AppSection.OrderModule.Actions.CancelOrderAction import CancelOrderAction
from src.Containers.AppSection.OrderModule.Actions.StartCreateOrderWorkflowAction import (
    StartCreateOrderWorkflowAction,
    ExecuteCreateOrderWorkflowAction,
)
from src.Containers.AppSection.OrderModule.Actions.GetOrderWorkflowStatusAction import (
    GetOrderWorkflowStatusAction,
    WaitForOrderWorkflowAction,
)
from src.Containers.AppSection.OrderModule.Queries.GetOrderQuery import GetOrderQuery
from src.Containers.AppSection.OrderModule.Queries.ListUserOrdersQuery import ListUserOrdersQuery
from src.Containers.AppSection.OrderModule.Data.Repositories.OrderRepository import OrderRepository
from src.Containers.AppSection.OrderModule.Data.Repositories.OrderItemRepository import OrderItemRepository
from src.Containers.AppSection.OrderModule.Data.UnitOfWork import OrderUnitOfWork
from src.Containers.AppSection.OrderModule.Tasks.InventoryTask import InventoryTask
from src.Containers.AppSection.OrderModule.Tasks.PaymentTask import PaymentTask
from src.Containers.AppSection.OrderModule.Tasks.NotificationTask import NotificationTask


class OrderModuleProvider(Provider):
    """Core provider for OrderModule - APP scope dependencies.
    
    Stateless services that can be reused across requests.
    Includes Temporal Client as singleton.
    """
    
    scope = Scope.APP
    
    # Tasks - stateless, reusable
    inventory_task = provide(InventoryTask)
    payment_task = provide(PaymentTask)
    notification_task = provide(NotificationTask)


class _BaseOrderRequestProvider(Provider):
    """Base provider with common REQUEST scope dependencies.
    
    Contains all dependencies shared between HTTP and CLI contexts.
    Not exported - use OrderRequestProvider or OrderCLIProvider instead.
    """
    
    scope = Scope.REQUEST
    
    # Repositories
    order_repository = provide(OrderRepository)
    order_item_repository = provide(OrderItemRepository)
    
    # Queries - CQRS read side
    @provide
    def get_order_query(
        self,
        order_repo: OrderRepository,
        item_repo: OrderItemRepository,
    ) -> GetOrderQuery:
        """Provide GetOrderQuery with repositories."""
        return GetOrderQuery(
            order_repository=order_repo,
            item_repository=item_repo,
        )
    
    @provide
    def list_user_orders_query(
        self,
        order_repo: OrderRepository,
    ) -> ListUserOrdersQuery:
        """Provide ListUserOrdersQuery with repository."""
        return ListUserOrdersQuery(order_repository=order_repo)
    
    # Actions - CQRS write side (need UoW, provided by subclass)
    @provide
    def create_order_action(
        self,
        uow: OrderUnitOfWork,
    ) -> CreateOrderAction:
        """Provide CreateOrderAction with UoW."""
        return CreateOrderAction(uow=uow)
    
    @provide
    def cancel_order_action(
        self,
        uow: OrderUnitOfWork,
    ) -> CancelOrderAction:
        """Provide CancelOrderAction with UoW."""
        return CancelOrderAction(uow=uow)
    
    # Temporal Workflow Actions
    @provide
    def start_create_order_workflow_action(
        self,
        temporal_client: TemporalClient,
    ) -> StartCreateOrderWorkflowAction:
        """Provide StartCreateOrderWorkflowAction with Temporal client."""
        return StartCreateOrderWorkflowAction(temporal_client=temporal_client)
    
    @provide
    def execute_create_order_workflow_action(
        self,
        temporal_client: TemporalClient,
    ) -> ExecuteCreateOrderWorkflowAction:
        """Provide ExecuteCreateOrderWorkflowAction with Temporal client."""
        return ExecuteCreateOrderWorkflowAction(temporal_client=temporal_client)
    
    @provide
    def get_order_workflow_status_action(
        self,
        temporal_client: TemporalClient,
    ) -> GetOrderWorkflowStatusAction:
        """Provide GetOrderWorkflowStatusAction with Temporal client."""
        return GetOrderWorkflowStatusAction(temporal_client=temporal_client)
    
    @provide
    def wait_for_order_workflow_action(
        self,
        temporal_client: TemporalClient,
    ) -> WaitForOrderWorkflowAction:
        """Provide WaitForOrderWorkflowAction with Temporal client."""
        return WaitForOrderWorkflowAction(temporal_client=temporal_client)


class OrderRequestProvider(_BaseOrderRequestProvider):
    """HTTP request-scoped provider for OrderModule.
    
    Extends base provider with UnitOfWork that has event emitter.
    """
    
    @provide
    def provide_order_uow(self, request: Request) -> OrderUnitOfWork:
        """Provide OrderUnitOfWork with event emitter from request."""
        return OrderUnitOfWork(_emit=request.app.emit, _app=request.app)


class OrderCLIProvider(_BaseOrderRequestProvider):
    """CLI-specific provider for OrderModule.
    
    Extends base provider with UnitOfWork without event emitter.
    """
    
    @provide
    def provide_order_uow(self) -> OrderUnitOfWork:
        """Provide OrderUnitOfWork without event emitter for CLI."""
        return OrderUnitOfWork(_emit=None, _app=None)


__all__ = [
    "OrderModuleProvider",
    "OrderRequestProvider",
    "OrderCLIProvider",
]

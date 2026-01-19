"""ProcessOrderSagaAction - Create order using saga pattern.

Orchestrates order creation as a distributed transaction with
automatic compensation on failure.
"""

import logfire
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Ship.Infrastructure.Saga import SagaOrchestrator, SagaContext
from src.Containers.AppSection.OrderModule.Data.Schemas.Requests import CreateOrderRequest
from src.Containers.AppSection.OrderModule.Sagas.CreateOrderSaga import (
    create_create_order_saga,
    CreateOrderSagaInput,
)
from src.Containers.AppSection.OrderModule.Tasks.ReserveInventoryTask import ReserveInventoryTask
from src.Containers.AppSection.OrderModule.Tasks.ProcessPaymentTask import ProcessPaymentTask
from src.Containers.AppSection.OrderModule.Tasks.SendNotificationTask import SendNotificationTask
from src.Containers.AppSection.OrderModule.Data.UnitOfWork import OrderUnitOfWork
from src.Containers.AppSection.OrderModule.Errors import OrderError


class ProcessOrderSagaAction(Action[CreateOrderRequest, SagaContext, OrderError]):
    """Use Case: Create order using saga pattern.
    
    Orchestrates order creation as a distributed transaction:
    1. Reserve inventory
    2. Process payment
    3. Create order record
    4. Send confirmation
    
    On failure at any step, automatically compensates previous steps:
    - Release inventory reservation
    - Refund payment
    - Mark order as failed
    
    Example:
        action = ProcessOrderSagaAction(
            reserve_inventory_task=reserve_inventory_task,
            process_payment_task=process_payment_task,
            order_uow=order_uow,
            send_notification_task=send_notification_task,
        )
        
        result = await action.run(CreateOrderRequest(...))
        
        match result:
            case Success(context):
                order_id = context.step_outputs["create_order"].id
            case Failure(error):
                logger.error(f"Order failed: {error}")
    """
    
    def __init__(
        self,
        reserve_inventory_task: ReserveInventoryTask,
        process_payment_task: ProcessPaymentTask,
        order_uow: OrderUnitOfWork,
        send_notification_task: SendNotificationTask,
    ) -> None:
        """Initialize action with dependencies.
        
        Args:
            reserve_inventory_task: Task for inventory operations
            process_payment_task: Task for payment processing
            order_uow: Unit of work for order persistence
            send_notification_task: Task for notifications
        """
        self.reserve_inventory_task = reserve_inventory_task
        self.process_payment_task = process_payment_task
        self.order_uow = order_uow
        self.send_notification_task = send_notification_task
    
    async def run(self, data: CreateOrderRequest) -> Result[SagaContext, OrderError]:
        """Execute order creation saga.
        
        Args:
            data: CreateOrderRequest with order details
            
        Returns:
            Result[SagaContext, OrderError]: Success with saga context or Failure
        """
        logfire.info(
            "🎭 Starting order creation saga",
            user_id=str(data.user_id),
            item_count=len(data.items),
            total_amount=str(data.total_amount),
        )
        
        # Create saga with injected dependencies
        saga = create_create_order_saga(
            reserve_inventory_task=self.reserve_inventory_task,
            process_payment_task=self.process_payment_task,
            order_uow=self.order_uow,
            send_notification_task=self.send_notification_task,
        )
        
        # Create orchestrator
        orchestrator = SagaOrchestrator(saga=saga)
        
        # Convert request to saga input
        saga_input = CreateOrderSagaInput(
            user_id=data.user_id,
            items=data.items,
            shipping_address=data.shipping_address,
            currency=data.currency,
            notes=data.notes,
        )
        
        # Execute saga
        result = await orchestrator.execute(saga_input)
        
        match result:
            case Success(context):
                logfire.info(
                    "✅ Order saga completed",
                    saga_id=str(context.saga_id),
                    order_id=str(context.step_outputs.get("create_order", {}).id) if context.step_outputs.get("create_order") else None,
                    duration_ms=context.duration_ms,
                )
                
                # Note: In a real app, would publish event here via UoW
                # But saga steps already publish their own events
                
                return Success(context)
            
            case Failure(error):
                logfire.error(
                    "❌ Order saga failed",
                    error=str(error),
                    code=getattr(error, "code", "UNKNOWN"),
                )
                
                return Failure(OrderError(
                    message=f"Order creation failed: {error.message}",
                    code=f"SAGA_{getattr(error, 'code', 'ERROR')}",
                ))


__all__ = ["ProcessOrderSagaAction"]

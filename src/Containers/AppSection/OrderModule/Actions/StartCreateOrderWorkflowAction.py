"""StartCreateOrderWorkflowAction - Start order creation via Temporal Workflow.

This Action starts the CreateOrderWorkflow in Temporal.
Returns immediately with workflow handle (async execution).

Architecture:
- Porto Action that starts Temporal Workflow
- Does NOT wait for workflow completion (async)
- Returns WorkflowHandle for tracking
- Use GetOrderWorkflowStatusQuery to check progress

Usage:
    action = StartCreateOrderWorkflowAction(temporal_client=client)
    result = await action.run(CreateOrderRequest(...))

    match result:
        case Success(info):
            print(f"Workflow started: {info.workflow_id}")
        case Failure(error):
            print(f"Failed to start: {error.message}")
"""

from dataclasses import dataclass
from uuid import UUID, uuid4

from pydantic import BaseModel
from returns.result import Failure, Result, Success
from temporalio.client import Client, WorkflowHandle

from src.Containers.AppSection.OrderModule.Activities.CreateOrderActivity import OrderItemInput
from src.Containers.AppSection.OrderModule.Data.Schemas.Requests import CreateOrderRequest
from src.Containers.AppSection.OrderModule.Errors import (
    OrderError,
    WorkflowStartError,
)
from src.Containers.AppSection.OrderModule.Workflows import (
    TASK_QUEUE,
    CreateOrderWorkflow,
    CreateOrderWorkflowInput,
)
from src.Ship.Parents.Action import Action

# =============================================================================
# Output DTO
# =============================================================================


class WorkflowStartedInfo(BaseModel):
    """Information about started workflow.

    Returned immediately after workflow starts.
    Use workflow_id to query status or wait for result.

    Attributes:
        workflow_id: Temporal workflow ID
        run_id: Temporal run ID (for this execution)
        order_id: Generated order UUID (for correlation)
        status: Initial status (always "started")
    """

    workflow_id: str
    run_id: str
    order_id: UUID
    status: str = "started"
    task_queue: str = TASK_QUEUE


# =============================================================================
# Action
# =============================================================================


@dataclass
class StartCreateOrderWorkflowAction(Action[CreateOrderRequest, WorkflowStartedInfo, OrderError]):
    """Start CreateOrder Temporal Workflow.

    This Action initiates the order creation saga via Temporal.
    The workflow runs asynchronously and can be tracked by its ID.

    Porto Architecture:
    - This is a Porto Action (Use Case)
    - Calls Temporal Client (external service)
    - Returns Result[T, E] for Railway-oriented error handling

    Temporal Benefits:
    - Durable execution (survives crashes)
    - Automatic retries per RetryPolicy
    - Built-in compensation handling
    - Full visibility and observability

    Example:
        action = StartCreateOrderWorkflowAction(temporal_client=client)

        result = await action.run(CreateOrderRequest(
            user_id=user.id,
            items=[...],
            shipping_address="123 Main St",
        ))

        match result:
            case Success(info):
                # Workflow started, can track by info.workflow_id
                pass
            case Failure(error):
                # Failed to start workflow
                pass
    """

    temporal_client: Client

    async def run(
        self,
        data: CreateOrderRequest,
    ) -> Result[WorkflowStartedInfo, OrderError]:
        """Start the CreateOrderWorkflow.

        Args:
            data: CreateOrderRequest with order details

        Returns:
            Result[WorkflowStartedInfo, OrderError]:
                Success with workflow info, or
                Failure with error details
        """
        # Generate unique workflow ID for correlation
        order_id = uuid4()
        workflow_id = f"order-{data.user_id}-{order_id}"

        # Convert request items to workflow input format
        workflow_items = [
            OrderItemInput(
                product_id=item.product_id,
                product_name=item.product_name,
                sku=item.sku,
                quantity=item.quantity,
                unit_price=str(item.unit_price),
            )
            for item in data.items
        ]

        # Build workflow input
        workflow_input = CreateOrderWorkflowInput(
            user_id=data.user_id,
            items=workflow_items,
            shipping_address=data.shipping_address,
            currency=data.currency,
            notes=data.notes,
            expedited_shipping=False,  # Could come from request
        )

        try:
            # Start workflow (async - returns immediately)
            handle: WorkflowHandle = await self.temporal_client.start_workflow(
                CreateOrderWorkflow.run,
                workflow_input,
                id=workflow_id,
                task_queue=TASK_QUEUE,
            )

            return Success(
                WorkflowStartedInfo(
                    workflow_id=handle.id,
                    run_id=handle.result_run_id or "",
                    order_id=order_id,
                    status="started",
                    task_queue=TASK_QUEUE,
                )
            )

        except Exception as e:
            return Failure(
                WorkflowStartError(
                    reason=str(e),
                    user_id=data.user_id,
                )
            )


# =============================================================================
# Sync Action (Wait for result)
# =============================================================================


class OrderWorkflowResultInfo(BaseModel):
    """Complete workflow result info.

    Returned after workflow completes (success or failure).
    """

    workflow_id: str
    order_id: UUID | None
    reservation_id: str | None
    payment_id: str | None
    delivery_id: str | None
    tracking_number: str | None
    status: str
    total_amount: str | None
    error: str | None = None


@dataclass
class ExecuteCreateOrderWorkflowAction(
    Action[CreateOrderRequest, OrderWorkflowResultInfo, OrderError]
):
    """Execute CreateOrder Workflow and wait for result.

    Unlike StartCreateOrderWorkflowAction, this action waits
    for the workflow to complete before returning.

    Use for:
    - Synchronous API calls that need the order result
    - Testing
    - Short-running workflows

    Avoid for:
    - Long-running workflows (use Start + Query instead)
    - When immediate response is needed
    """

    temporal_client: Client

    async def run(
        self,
        data: CreateOrderRequest,
    ) -> Result[OrderWorkflowResultInfo, OrderError]:
        """Execute workflow and wait for result.

        Args:
            data: CreateOrderRequest with order details

        Returns:
            Result with complete workflow outcome
        """
        # Generate IDs
        order_id = uuid4()
        workflow_id = f"order-{data.user_id}-{order_id}"

        # Convert items
        workflow_items = [
            OrderItemInput(
                product_id=item.product_id,
                product_name=item.product_name,
                sku=item.sku,
                quantity=item.quantity,
                unit_price=str(item.unit_price),
            )
            for item in data.items
        ]

        workflow_input = CreateOrderWorkflowInput(
            user_id=data.user_id,
            items=workflow_items,
            shipping_address=data.shipping_address,
            currency=data.currency,
            notes=data.notes,
        )

        try:
            # Start workflow
            handle = await self.temporal_client.start_workflow(
                CreateOrderWorkflow.run,
                workflow_input,
                id=workflow_id,
                task_queue=TASK_QUEUE,
            )

            # Wait for result
            result = await handle.result()

            # Result is Result[OrderWorkflowResult, OrderWorkflowError]
            match result:
                case Success(workflow_result):
                    return Success(
                        OrderWorkflowResultInfo(
                            workflow_id=workflow_id,
                            order_id=workflow_result.order_id,
                            reservation_id=workflow_result.reservation_id,
                            payment_id=workflow_result.payment_id,
                            delivery_id=workflow_result.delivery_id,
                            tracking_number=workflow_result.tracking_number,
                            status=workflow_result.status,
                            total_amount=workflow_result.total_amount,
                        )
                    )
                case Failure(workflow_error):
                    return Success(
                        OrderWorkflowResultInfo(
                            workflow_id=workflow_id,
                            order_id=None,
                            reservation_id=None,
                            payment_id=None,
                            delivery_id=None,
                            tracking_number=None,
                            status="failed",
                            total_amount=None,
                            error=workflow_error.message,
                        )
                    )
                case _:
                    # Handle raw result (for non-Result returns)
                    return Success(
                        OrderWorkflowResultInfo(
                            workflow_id=workflow_id,
                            order_id=getattr(result, "order_id", None),
                            reservation_id=getattr(result, "reservation_id", None),
                            payment_id=getattr(result, "payment_id", None),
                            delivery_id=getattr(result, "delivery_id", None),
                            tracking_number=getattr(result, "tracking_number", None),
                            status=getattr(result, "status", "unknown"),
                            total_amount=getattr(result, "total_amount", None),
                        )
                    )

        except Exception as e:
            return Failure(
                WorkflowStartError(
                    reason=str(e),
                    user_id=data.user_id,
                )
            )


__all__ = [
    "ExecuteCreateOrderWorkflowAction",
    "OrderWorkflowResultInfo",
    "StartCreateOrderWorkflowAction",
    "WorkflowStartedInfo",
]

"""GetOrderWorkflowStatusAction - Query Temporal Workflow status.

This Action queries the current status of a running workflow.
Uses Temporal's query mechanism for real-time status.

Architecture:
- Porto Action for querying workflow state
- Uses Temporal Client to get workflow handle
- Queries workflow status via Temporal query mechanism
"""

import contextlib
from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel
from returns.result import Failure, Result, Success
from temporalio.client import Client, WorkflowExecutionStatus

from src.Containers.AppSection.OrderModule.Errors import (
    OrderError,
    WorkflowNotFoundError,
    WorkflowQueryError,
)
from src.Ship.Parents.Action import Action

# =============================================================================
# Input/Output DTOs
# =============================================================================


class GetWorkflowStatusInput(BaseModel):
    """Input for workflow status query.

    Attributes:
        workflow_id: Temporal workflow ID to query
    """

    workflow_id: str


class WorkflowStatusInfo(BaseModel):
    """Workflow status information.

    Contains current state of the workflow execution.

    Attributes:
        workflow_id: Temporal workflow ID
        status: Workflow execution status
        current_step: Current step being executed (if available)
        order_id: Order UUID if created
        is_running: Whether workflow is still running
        close_time: When workflow completed (if finished)
    """

    workflow_id: str
    status: str  # running, completed, failed, cancelled, terminated
    current_step: str | None = None
    order_id: UUID | None = None
    is_running: bool = True
    close_time: str | None = None

    # Execution details
    run_id: str | None = None
    task_queue: str | None = None


# =============================================================================
# Action
# =============================================================================


@dataclass
class GetOrderWorkflowStatusAction(Action[GetWorkflowStatusInput, WorkflowStatusInfo, OrderError]):
    """Get current status of order workflow.

    This Action queries Temporal for the workflow's current state.
    Can be used for:
    - Progress tracking UI
    - Polling for completion
    - Debugging workflow issues

    Example:
        action = GetOrderWorkflowStatusAction(temporal_client=client)

        result = await action.run(GetWorkflowStatusInput(
            workflow_id="order-user123-abc456"
        ))

        match result:
            case Success(info):
                if info.is_running:
                    print(f"Workflow running, step: {info.current_step}")
                else:
                    print(f"Workflow {info.status}")
            case Failure(error):
                print(f"Query failed: {error.message}")
    """

    temporal_client: Client

    async def run(
        self,
        data: GetWorkflowStatusInput,
    ) -> Result[WorkflowStatusInfo, OrderError]:
        """Query workflow status.

        Args:
            data: Input with workflow_id

        Returns:
            Result[WorkflowStatusInfo, OrderError]
        """
        try:
            # Get workflow handle
            handle = self.temporal_client.get_workflow_handle(data.workflow_id)

            # Get workflow description
            desc = await handle.describe()

            # Map Temporal status to string
            status_map = {
                WorkflowExecutionStatus.RUNNING: "running",
                WorkflowExecutionStatus.COMPLETED: "completed",
                WorkflowExecutionStatus.FAILED: "failed",
                WorkflowExecutionStatus.CANCELED: "cancelled",
                WorkflowExecutionStatus.TERMINATED: "terminated",
                WorkflowExecutionStatus.CONTINUED_AS_NEW: "continued",
                WorkflowExecutionStatus.TIMED_OUT: "timed_out",
            }

            status_str = status_map.get(desc.status, "unknown")
            is_running = desc.status == WorkflowExecutionStatus.RUNNING

            # Try to query current step if workflow is running
            current_step = None
            order_id = None

            if is_running:
                with contextlib.suppress(Exception):
                    current_step = await handle.query("get_status")

                with contextlib.suppress(Exception):
                    order_id = await handle.query("get_order_id")

            close_time = None
            if desc.close_time:
                close_time = desc.close_time.isoformat()

            return Success(
                WorkflowStatusInfo(
                    workflow_id=data.workflow_id,
                    status=status_str,
                    current_step=current_step,
                    order_id=order_id,
                    is_running=is_running,
                    close_time=close_time,
                    run_id=desc.run_id,
                    task_queue=desc.task_queue,
                )
            )

        except Exception as e:
            error_msg = str(e)

            if "not found" in error_msg.lower():
                return Failure(
                    WorkflowNotFoundError(
                        workflow_id=data.workflow_id,
                    )
                )

            return Failure(
                WorkflowQueryError(
                    workflow_id=data.workflow_id,
                    reason=error_msg,
                )
            )


# =============================================================================
# Query for waiting on result
# =============================================================================


@dataclass
class WaitForOrderWorkflowAction(Action[GetWorkflowStatusInput, WorkflowStatusInfo, OrderError]):
    """Wait for workflow to complete and return final status.

    Unlike GetOrderWorkflowStatusAction, this action blocks
    until the workflow finishes.

    Use for:
    - Synchronous completion checks
    - Testing
    """

    temporal_client: Client

    async def run(
        self,
        data: GetWorkflowStatusInput,
    ) -> Result[WorkflowStatusInfo, OrderError]:
        """Wait for workflow completion.

        Args:
            data: Input with workflow_id

        Returns:
            Result with final workflow status
        """
        try:
            handle = self.temporal_client.get_workflow_handle(data.workflow_id)

            # Wait for result (blocks until complete)
            try:
                result = await handle.result()
            except Exception:
                # Workflow failed
                desc = await handle.describe()
                return Success(
                    WorkflowStatusInfo(
                        workflow_id=data.workflow_id,
                        status="failed",
                        current_step=None,
                        order_id=None,
                        is_running=False,
                        close_time=desc.close_time.isoformat() if desc.close_time else None,
                        run_id=desc.run_id,
                        task_queue=desc.task_queue,
                    )
                )

            # Get final description
            desc = await handle.describe()

            # Extract order_id from result if available
            order_id = None
            if hasattr(result, "order_id"):
                order_id = result.order_id
            elif hasattr(result, "value") and hasattr(result.value, "order_id"):
                order_id = result.value.order_id

            return Success(
                WorkflowStatusInfo(
                    workflow_id=data.workflow_id,
                    status="completed",
                    current_step=None,
                    order_id=order_id,
                    is_running=False,
                    close_time=desc.close_time.isoformat() if desc.close_time else None,
                    run_id=desc.run_id,
                    task_queue=desc.task_queue,
                )
            )

        except Exception as e:
            error_msg = str(e)

            if "not found" in error_msg.lower():
                return Failure(
                    WorkflowNotFoundError(
                        workflow_id=data.workflow_id,
                    )
                )

            return Failure(
                WorkflowQueryError(
                    workflow_id=data.workflow_id,
                    reason=error_msg,
                )
            )


__all__ = [
    "GetOrderWorkflowStatusAction",
    "GetWorkflowStatusInput",
    "WaitForOrderWorkflowAction",
    "WorkflowStatusInfo",
]

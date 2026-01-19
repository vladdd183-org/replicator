"""Order API Controller.

HTTP endpoints for order operations including Temporal Workflow-based order creation.

Endpoints:
- GET /orders/{id} - Get order by ID
- GET /orders/user/{user_id} - List user's orders
- POST /orders - Create simple order (no saga)
- POST /orders/workflow - Start order creation workflow (async)
- POST /orders/workflow/sync - Execute workflow and wait for result
- GET /orders/workflow/{workflow_id}/status - Get workflow status
- DELETE /orders/{id} - Cancel order
"""

from uuid import UUID

from dishka.integrations.litestar import FromDishka
from litestar import Controller, delete, get, post
from litestar.response import Response
from returns.result import Result

from src.Containers.AppSection.OrderModule.Actions.CancelOrderAction import (
    CancelOrderAction,
    CancelOrderInput,
)
from src.Containers.AppSection.OrderModule.Actions.CreateOrderAction import CreateOrderAction
from src.Containers.AppSection.OrderModule.Actions.GetOrderWorkflowStatusAction import (
    GetOrderWorkflowStatusAction,
    GetWorkflowStatusInput,
    WorkflowStatusInfo,
)
from src.Containers.AppSection.OrderModule.Actions.StartCreateOrderWorkflowAction import (
    ExecuteCreateOrderWorkflowAction,
    OrderWorkflowResultInfo,
    StartCreateOrderWorkflowAction,
    WorkflowStartedInfo,
)
from src.Containers.AppSection.OrderModule.Data.Schemas.Requests import (
    CancelOrderRequest,
    CreateOrderRequest,
)
from src.Containers.AppSection.OrderModule.Data.Schemas.Responses import (
    OrderListResponse,
    OrderResponse,
    WorkflowResultResponse,
    WorkflowStartedResponse,
    WorkflowStatusResponse,
)
from src.Containers.AppSection.OrderModule.Errors import OrderError
from src.Containers.AppSection.OrderModule.Models.Order import Order
from src.Containers.AppSection.OrderModule.Queries.GetOrderQuery import (
    GetOrderInput,
    GetOrderQuery,
)
from src.Containers.AppSection.OrderModule.Queries.ListUserOrdersQuery import (
    ListUserOrdersInput,
    ListUserOrdersQuery,
)
from src.Ship.Decorators.result_handler import result_handler


class OrderController(Controller):
    """Controller for order operations.

    Provides REST API endpoints for:
    - Creating orders (simple and saga-based)
    - Retrieving orders
    - Cancelling orders
    """

    path = "/orders"
    tags = ["Orders"]

    # ==========================================================================
    # Query Endpoints (GET)
    # ==========================================================================

    @get("/{order_id:uuid}")
    async def get_order(
        self,
        order_id: UUID,
        query: FromDishka[GetOrderQuery],
    ) -> Response:
        """Get order by ID.

        Args:
            order_id: UUID of the order
            query: Injected GetOrderQuery

        Returns:
            Order details or 404 if not found
        """
        result = await query.execute(GetOrderInput(order_id=order_id))

        if result is None:
            return Response(
                content={"error": f"Order {order_id} not found", "code": "ORDER_NOT_FOUND"},
                status_code=404,
            )

        return Response(
            content=OrderResponse.from_entity(result.order, result.items).model_dump(mode="json"),
            status_code=200,
        )

    @get("/user/{user_id:uuid}")
    async def list_user_orders(
        self,
        user_id: UUID,
        query: FromDishka[ListUserOrdersQuery],
        limit: int = 50,
        offset: int = 0,
    ) -> Response:
        """List orders for a user.

        Args:
            user_id: UUID of the user
            query: Injected ListUserOrdersQuery
            limit: Maximum results
            offset: Pagination offset

        Returns:
            Paginated list of orders
        """
        result = await query.execute(
            ListUserOrdersInput(
                user_id=user_id,
                limit=min(limit, 100),
                offset=offset,
            )
        )

        orders = [OrderResponse.from_entity(order) for order in result.orders]

        return Response(
            content=OrderListResponse(
                orders=orders,
                total=result.total,
                limit=result.limit,
                offset=result.offset,
            ).model_dump(mode="json"),
            status_code=200,
        )

    # ==========================================================================
    # Command Endpoints (POST, DELETE) - Use @result_handler
    # ==========================================================================

    @post("/")
    @result_handler(OrderResponse, success_status=201)
    async def create_order(
        self,
        data: CreateOrderRequest,
        action: FromDishka[CreateOrderAction],
    ) -> Result[Order, OrderError]:
        """Create a simple order.

        For distributed transactions, use POST /orders/saga instead.

        Args:
            data: CreateOrderRequest with order details
            action: Injected CreateOrderAction

        Returns:
            Created order or error
        """
        return await action.run(data)

    # ==========================================================================
    # Temporal Workflow Endpoints
    # ==========================================================================

    @post("/workflow")
    @result_handler(WorkflowStartedResponse, success_status=202)
    async def start_order_workflow(
        self,
        data: CreateOrderRequest,
        action: FromDishka[StartCreateOrderWorkflowAction],
    ) -> Result[WorkflowStartedInfo, OrderError]:
        """Start order creation via Temporal Workflow (async).

        Returns immediately with workflow ID.
        Use GET /orders/workflow/{id}/status to check progress.

        Benefits over sync:
        - Non-blocking (returns immediately)
        - Durable (survives crashes)
        - Trackable (query status anytime)

        Args:
            data: CreateOrderRequest with order details
            action: Injected StartCreateOrderWorkflowAction

        Returns:
            202 Accepted with workflow info
        """
        return await action.run(data)

    @post("/workflow/sync")
    @result_handler(WorkflowResultResponse, success_status=201)
    async def execute_order_workflow(
        self,
        data: CreateOrderRequest,
        action: FromDishka[ExecuteCreateOrderWorkflowAction],
    ) -> Result[OrderWorkflowResultInfo, OrderError]:
        """Execute order creation workflow and wait for result.

        Blocks until workflow completes.
        Use for testing or when sync response is required.

        For production, prefer POST /orders/workflow (async).

        Args:
            data: CreateOrderRequest with order details
            action: Injected ExecuteCreateOrderWorkflowAction

        Returns:
            201 Created with complete order result
        """
        return await action.run(data)

    @get("/workflow/{workflow_id:str}/status")
    @result_handler(WorkflowStatusResponse, success_status=200)
    async def get_workflow_status(
        self,
        workflow_id: str,
        action: FromDishka[GetOrderWorkflowStatusAction],
    ) -> Result[WorkflowStatusInfo, OrderError]:
        """Get current status of order workflow.

        Returns workflow execution status including:
        - Current step being executed
        - Order ID (if created)
        - Running/completed/failed status

        Args:
            workflow_id: Temporal workflow ID
            action: Injected GetOrderWorkflowStatusAction

        Returns:
            Workflow status info
        """
        return await action.run(GetWorkflowStatusInput(workflow_id=workflow_id))

    @delete("/{order_id:uuid}")
    @result_handler(OrderResponse, success_status=200)
    async def cancel_order(
        self,
        order_id: UUID,
        data: CancelOrderRequest,
        action: FromDishka[CancelOrderAction],
    ) -> Result[Order, OrderError]:
        """Cancel an order.

        Cancels order if in cancellable state.
        Triggers refund and inventory release.

        Args:
            order_id: UUID of the order to cancel
            data: CancelOrderRequest with reason
            action: Injected CancelOrderAction

        Returns:
            Cancelled order or error
        """
        return await action.run(
            CancelOrderInput(
                order_id=order_id,
                reason=data.reason,
                request_refund=data.request_refund,
            )
        )


__all__ = ["OrderController"]

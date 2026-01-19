"""OrderModule Temporal Workflows.

Workflows are durable, long-running processes orchestrated by Temporal.
Each Workflow is a distributed transaction with automatic compensation.

Temporal Workflows используются когда:
- Нужен откат (compensation) при ошибках
- Нужна оркестрация нескольких шагов
- Нужна гарантия выполнения (at-least-once)
- Процесс может длиться долго (минуты, часы)
- Нужна visibility и observability

Workflows in this module:
- CreateOrderWorkflow: Order creation saga with compensation

Architecture:
- Workflow = Сложный Porto Action с Saga
- Activities = Porto Tasks
- Worker executes Activities and Workflows

Usage:
    from temporalio.client import Client
    
    client = await Client.connect("localhost:7233")
    
    # Start workflow
    handle = await client.start_workflow(
        CreateOrderWorkflow.run,
        CreateOrderWorkflowInput(...),
        id=f"order-{uuid4()}",
        task_queue="orders",
    )
    
    # Wait for result
    result = await handle.result()
"""

from src.Containers.AppSection.OrderModule.Workflows.CreateOrderWorkflow import (
    CreateOrderWorkflow,
    CreateOrderWorkflowInput,
    OrderWorkflowResult,
    OrderWorkflowError,
    ALL_WORKFLOWS,
)


# Task queue name for this module's workflows
TASK_QUEUE = "orders"


__all__ = [
    "CreateOrderWorkflow",
    "CreateOrderWorkflowInput",
    "OrderWorkflowResult",
    "OrderWorkflowError",
    "ALL_WORKFLOWS",
    "TASK_QUEUE",
]

"""Order module sagas.

DEPRECATED: This module contains the legacy TaskIQ-based Saga implementation.
For new code, use Temporal Workflows instead:

    from src.Containers.AppSection.OrderModule.Workflows import (
        CreateOrderWorkflow,
        CreateOrderWorkflowInput,
    )
    from src.Containers.AppSection.OrderModule.Actions import (
        StartCreateOrderWorkflowAction,
    )

Migration guide:
1. Replace ProcessOrderSagaAction with StartCreateOrderWorkflowAction
2. Replace POST /orders/saga with POST /orders/workflow
3. Use Temporal dashboard for monitoring

The legacy Saga is kept for backwards compatibility but will be removed
in a future version.
"""

import warnings

warnings.warn(
    "OrderModule.Sagas is deprecated. Use OrderModule.Workflows with Temporal instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.Containers.AppSection.OrderModule.Sagas.CreateOrderSaga import (
    CreateOrderSaga,
    create_order_saga_factory,
    CreateOrderSagaInput,
    CreateOrderSagaOutput,
)

__all__ = [
    "CreateOrderSaga",
    "create_order_saga_factory",
    "CreateOrderSagaInput",
    "CreateOrderSagaOutput",
]

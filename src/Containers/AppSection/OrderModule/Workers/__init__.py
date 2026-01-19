"""OrderModule Temporal Workers.

This module contains Temporal Worker configuration for OrderModule.

The Worker executes:
- CreateOrderWorkflow
- All Activities (create_order, reserve_inventory, charge_payment, etc.)

To run the worker:
    python -m src.Containers.AppSection.OrderModule.Workers.run

Or via CLI:
    python -m src.Ship.CLI.Main worker order
"""

from src.Containers.AppSection.OrderModule.Workers.OrderWorker import (
    create_order_worker,
    run_order_worker,
    ORDER_TASK_QUEUE,
)


__all__ = [
    "create_order_worker",
    "run_order_worker",
    "ORDER_TASK_QUEUE",
]

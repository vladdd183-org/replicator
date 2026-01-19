"""OrderModule — E-commerce order management with Temporal Workflows.

This module provides:
- Order creation with distributed transaction support (Temporal Saga pattern)
- Inventory reservation via Activities
- Payment processing via Activities
- Delivery scheduling via Activities
- Order lifecycle management

Architecture:
- Workflows: CreateOrderWorkflow (durable saga with compensation)
- Activities: Atomic operations (create_order, reserve_inventory, etc.)
- Actions: Use cases that start workflows or perform simple operations
- Queries: CQRS read models for order retrieval

Key components:
- CreateOrderWorkflow: Temporal workflow with automatic compensation
- Activities: create_order, reserve_inventory, charge_payment, schedule_delivery
- StartCreateOrderWorkflowAction: Starts workflow asynchronously
- OrderController: HTTP API endpoints

Running the Worker:
    python -m src.Containers.AppSection.OrderModule.Workers.run

API Endpoints:
- POST /orders - Simple order creation (no saga)
- POST /orders/workflow - Start order workflow (async)
- POST /orders/workflow/sync - Execute workflow and wait
- GET /orders/workflow/{id}/status - Check workflow status
- GET /orders/{id} - Get order by ID
- DELETE /orders/{id} - Cancel order
"""

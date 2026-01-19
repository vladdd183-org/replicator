"""Parent classes for all components.

Hyper-Porto base classes following Porto architecture pattern.

Components:
- Action: Use Case / Command handler, returns Result[T, E]
- Task: Atomic reusable operation (sync or async)
- Query: CQRS read operation, no side effects
- Repository: Data access abstraction
- Model: Piccolo ORM table base
- UnitOfWork: Transaction boundary with domain events
- DomainEvent: Event for async module communication
- Gateway: Inter-module synchronous communication (Ports & Adapters)
"""

from src.Ship.Parents.Action import Action
from src.Ship.Parents.Task import Task, SyncTask
from src.Ship.Parents.Query import Query, SyncQuery
from src.Ship.Parents.Repository import Repository
from src.Ship.Parents.Model import Model
from src.Ship.Parents.UnitOfWork import BaseUnitOfWork
from src.Ship.Parents.Event import DomainEvent
from src.Ship.Parents.Gateway import (
    GatewayProtocol,
    BaseGateway,
    DirectAdapterBase,
    HttpAdapterBase,
    GrpcAdapterBase,
)

__all__ = [
    # Core components
    "Action",
    "Task",
    "SyncTask",
    "Query",
    "SyncQuery",
    "Repository",
    "Model",
    "BaseUnitOfWork",
    "DomainEvent",
    # Gateway components
    "GatewayProtocol",
    "BaseGateway",
    "DirectAdapterBase",
    "HttpAdapterBase",
    "GrpcAdapterBase",
]


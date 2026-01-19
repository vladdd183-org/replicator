"""Ship Core module.

Core types, protocols, and base schemas.
"""

from src.Ship.Core.BaseSchema import EntitySchema
from src.Ship.Core.Errors import (
    BaseError,
    DomainException,
    NotFoundError,
    ValidationError,
    AlreadyExistsError,
    UnauthorizedError,
    ForbiddenError,
    ConflictError,
)
from src.Ship.Core.Types import DomainEvent, Entity, Identifiable
from src.Ship.Core.Protocols import (
    RepositoryProtocol,
    UnitOfWorkProtocol,
)

__all__ = [
    # Base schema
    "EntitySchema",
    # Errors
    "BaseError",
    "DomainException",
    "NotFoundError",
    "ValidationError",
    "AlreadyExistsError",
    "UnauthorizedError",
    "ForbiddenError",
    "ConflictError",
    # Types
    "DomainEvent",
    "Entity",
    "Identifiable",
    # Protocols
    "RepositoryProtocol",
    "UnitOfWorkProtocol",
]


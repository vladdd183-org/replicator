"""Ship Core module.

Core types, protocols, and base schemas.
"""

from src.Ship.Core.BaseSchema import EntitySchema
from src.Ship.Core.Errors import (
    BaseError,
    ErrorWithTemplate,
    DomainException,
    NotFoundError,
    ValidationError,
    AlreadyExistsError,
    UnauthorizedError,
    ForbiddenError,
    ConflictError,
    UnexpectedError,
)
from src.Ship.Core.GatewayErrors import (
    GatewayError,
    GatewayConnectionError,
    GatewayTimeoutError,
    GatewayUnavailableError,
    GatewayResponseError,
    GatewayAuthenticationError,
    GatewayCircuitOpenError,
    GatewayRateLimitError,
    GatewayServerError,
    GatewayClientError,
)
from src.Ship.Core.Types import DomainEvent, Entity, Identifiable
from src.Ship.Core.Protocols import (
    RepositoryProtocol,
    UnitOfWorkProtocol,
)

__all__ = [
    # Base schema
    "EntitySchema",
    # Base Errors
    "BaseError",
    "ErrorWithTemplate",
    "DomainException",
    "NotFoundError",
    "ValidationError",
    "AlreadyExistsError",
    "UnauthorizedError",
    "ForbiddenError",
    "ConflictError",
    "UnexpectedError",
    # Gateway Errors
    "GatewayError",
    "GatewayConnectionError",
    "GatewayTimeoutError",
    "GatewayUnavailableError",
    "GatewayResponseError",
    "GatewayAuthenticationError",
    "GatewayCircuitOpenError",
    "GatewayRateLimitError",
    "GatewayServerError",
    "GatewayClientError",
    # Types
    "DomainEvent",
    "Entity",
    "Identifiable",
    # Protocols
    "RepositoryProtocol",
    "UnitOfWorkProtocol",
]


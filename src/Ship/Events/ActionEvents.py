"""Action-related events for Ship layer.

These events enable cross-container communication for auditing
without violating Porto's container isolation principles.

According to Porto:
- Containers communicate via events (not direct imports)
- Ship layer provides shared interfaces and events
- AuditModule listens to these Ship-level events
"""

from typing import Any
from uuid import UUID

from src.Ship.Parents.Event import DomainEvent


class ActionExecuted(DomainEvent):
    """Event published when any action is executed.
    
    This is a Ship-level event that allows AuditModule to
    track all action executions without other containers
    importing from AuditModule.
    
    Flow:
        1. @audited decorator wraps Action.run()
        2. After execution, decorator publishes ActionExecuted
        3. AuditModule listener receives event
        4. Listener creates AuditLog entry
    
    Attributes:
        action_name: Name of the action (e.g., "create_user")
        entity_type: Type of entity affected (e.g., "User")
        entity_id: ID of the affected entity (if available)
        actor_id: User who performed the action
        actor_email: Email of the actor
        status: "success" or "failure"
        input_data: Input data (with sensitive fields redacted)
        output_data: Output data or error info
        duration_ms: Execution time in milliseconds
        
    Example:
        event = ActionExecuted(
            action_name="create_user",
            entity_type="User",
            entity_id="123e4567-e89b-12d3-a456-426614174000",
            actor_id=current_user.id,
            status="success",
            input_data={"email": "user@example.com", "name": "John"},
        )
    """
    
    action_name: str
    entity_type: str | None = None
    entity_id: str | None = None
    actor_id: UUID | None = None
    actor_email: str | None = None
    status: str = "success"  # "success" or "failure"
    input_data: dict[str, Any] | None = None
    output_data: dict[str, Any] | None = None
    duration_ms: float | None = None
    request_id: str | None = None  # For correlation
    ip_address: str | None = None
    user_agent: str | None = None




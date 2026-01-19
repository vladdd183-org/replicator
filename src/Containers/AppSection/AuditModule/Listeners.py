"""Event listeners for AuditModule.

These listeners handle Ship-level ActionExecuted events and
create audit log entries. This follows Porto's event-driven
communication pattern for cross-container interaction.

Architecture:
    Ship/Decorators/audited.py  →  publishes ActionExecuted via UoW
                    ↓
    AuditModule/Listeners.py    →  receives event, creates AuditLog

Registration:
    These listeners are registered in src/App.py via Litestar events.
"""

from typing import TYPE_CHECKING, Any
from uuid import UUID

import logfire

from litestar.events import listener

from src.Ship.Events.ActionEvents import ActionExecuted
from src.Containers.AppSection.AuditModule.Models.AuditLog import AuditLog

if TYPE_CHECKING:
    from litestar import Litestar


@listener(ActionExecuted.__name__)
async def on_action_executed(
    action_name: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    actor_id: str | None = None,
    actor_email: str | None = None,
    status: str = "success",
    input_data: dict[str, Any] | None = None,
    output_data: dict[str, Any] | None = None,
    duration_ms: float | None = None,
    request_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    occurred_at: str | None = None,
    app: "Litestar | None" = None,  # Passed from UoW emit
    **kwargs: Any,  # Ignore any extra fields
) -> None:
    """Handle ActionExecuted events from Ship layer.
    
    Creates an AuditLog entry whenever any action decorated with
    @audited is executed. This allows any container to be audited
    without importing from AuditModule.
    
    Note: Litestar events pass kwargs from model_dump(), so we accept
    individual fields instead of the event object.
    
    Example:
        # In UserModule:
        from src.Ship.Decorators import audited
        
        @audited(action="create", entity_type="User")
        class CreateUserAction(Action[...]):
            ...
        
        # When action runs, this listener receives event
        # and creates AuditLog entry automatically
    """
    try:
        # Convert actor_id string to UUID if present
        parsed_actor_id: UUID | None = None
        if actor_id:
            try:
                parsed_actor_id = UUID(actor_id)
            except (ValueError, TypeError):
                pass
        
        audit_log = AuditLog(
            actor_id=parsed_actor_id,
            actor_email=actor_email,
            action=action_name,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=None,
            new_values=input_data,
            metadata={
                "status": status,
                "duration_ms": duration_ms,
                "request_id": request_id,
                **(output_data or {}),
            } if output_data or duration_ms else None,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await audit_log.save()
        
        logfire.debug(
            "Audit log created for action",
            action=action_name,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
        )
        
    except Exception as e:
        # Don't let audit logging failures break the application
        logfire.error(
            "Failed to create audit log from event",
            error=str(e),
            action=action_name,
        )


# Export listeners for registration
audit_listeners = [
    on_action_executed,
]

__all__ = ["on_action_executed", "audit_listeners"]


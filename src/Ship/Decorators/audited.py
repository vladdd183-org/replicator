"""Audited decorator for automatic action logging (Ship Layer).

This decorator lives in Ship layer to allow any container to use it
without creating direct dependencies between containers.

The decorator publishes ActionExecuted events, which AuditModule
listens to and persists. This follows Porto's event-driven
communication pattern for cross-container interaction.

Architecture:
    Ship/Decorators/audited.py  →  publishes ActionExecuted event
                    ↓
    AuditModule/Listeners.py    →  receives event, creates AuditLog

Example:
    from src.Ship.Decorators.audited import audited

    @audited(action="create_user", entity_type="User")
    class CreateUserAction(Action[CreateUserRequest, User, UserError]):
        async def run(self, data: CreateUserRequest) -> Result[User, UserError]:
            ...

Benefits:
    - No direct imports from AuditModule
    - Follows Porto's event-driven pattern
    - Containers remain loosely coupled
    - Easy to disable auditing (just don't register listener)
"""

import time
from functools import wraps
from typing import TypeVar, Callable, Any
from uuid import UUID

import logfire
from returns.result import Result, Success, Failure

from src.Ship.Events.ActionEvents import ActionExecuted

T = TypeVar("T")
E = TypeVar("E")

# List of sensitive field names to redact
SENSITIVE_FIELDS = frozenset({
    "password", "secret", "token", "api_key", "apikey",
    "access_token", "refresh_token", "private_key",
    "credit_card", "cvv", "ssn", "pin",
})


def _redact_sensitive(data: dict[str, Any]) -> dict[str, Any]:
    """Redact sensitive fields from data dictionary.
    
    Args:
        data: Dictionary to redact
        
    Returns:
        Dictionary with sensitive values replaced by "***REDACTED***"
    """
    result = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_FIELDS:
            result[key] = "***REDACTED***"
        elif isinstance(value, dict):
            result[key] = _redact_sensitive(value)
        else:
            result[key] = value
    return result


def audited(
    action: str,
    entity_type: str | None = None,
    capture_input: bool = True,
    capture_output: bool = False,
) -> Callable[[type], type]:
    """Decorator for auditing Action classes.
    
    Wraps the `run` method of an Action to automatically publish
    ActionExecuted events. AuditModule listens to these events
    and creates audit log entries.
    
    This decorator is in Ship layer, so any container can use it
    without importing from AuditModule (follows Porto principles).
    
    Args:
        action: Action name (e.g., "create", "update", "delete")
        entity_type: Type of entity being affected
        capture_input: Whether to include input data in event
        capture_output: Whether to include output data in event
        
    Returns:
        Decorated class with audited run method
        
    Example:
        @audited(action="create", entity_type="User")
        class CreateUserAction(Action[CreateUserRequest, User, UserError]):
            async def run(self, data: CreateUserRequest) -> Result[User, UserError]:
                ...
                
    Note:
        The decorator stores the event publisher function on the action
        instance. If you need to customize publishing, you can set
        `self._audit_publisher` before calling run().
    """
    def decorator(cls: type) -> type:
        original_run = cls.run
        
        @wraps(original_run)
        async def audited_run(self, data: Any) -> Result[T, E]:
            start_time = time.monotonic()
            
            # Extract actor info if available
            actor_id: UUID | None = None
            actor_email: str | None = None
            
            if hasattr(self, "current_user") and self.current_user:
                actor_id = getattr(self.current_user, "id", None)
                actor_email = getattr(self.current_user, "email", None)
            
            # Prepare input data
            input_data: dict | None = None
            if capture_input and data:
                try:
                    if hasattr(data, "model_dump"):
                        input_data = _redact_sensitive(data.model_dump(mode="json"))
                    else:
                        input_data = {"raw": str(data)[:500]}  # Limit size
                except Exception:
                    input_data = None
            
            # Execute the actual action
            result = await original_run(self, data)
            
            # Calculate duration
            duration_ms = (time.monotonic() - start_time) * 1000
            
            # Extract result info
            entity_id: str | None = None
            output_data: dict | None = None
            status = "success"
            
            match result:
                case Success(value):
                    if value:
                        # Try to get ID from result
                        if hasattr(value, "id"):
                            entity_id = str(value.id)
                        elif isinstance(value, dict):
                            entity_id = str(value.get("id", ""))
                        
                        if capture_output:
                            try:
                                if hasattr(value, "model_dump"):
                                    output_data = value.model_dump(mode="json")
                            except Exception:
                                pass
                
                case Failure(error):
                    status = "failure"
                    if hasattr(error, "model_dump"):
                        output_data = {"error": error.model_dump(mode="json")}
                    else:
                        output_data = {"error": str(error)}
            
            # Create event
            event = ActionExecuted(
                action_name=f"{action}_{status}",
                entity_type=entity_type,
                entity_id=entity_id,
                actor_id=actor_id,
                actor_email=actor_email,
                status=status,
                input_data=input_data,
                output_data=output_data if status == "failure" or capture_output else None,
                duration_ms=duration_ms,
            )
            
            # Publish event through UoW's emit function if available
            # This works because UoW has _emit from Litestar DI
            if hasattr(self, "uow") and hasattr(self.uow, "_emit") and self.uow._emit is not None:
                # Publish directly via Litestar emit (not through add_event which requires open transaction)
                self.uow._emit(
                    event.event_name,
                    app=getattr(self.uow, "_app", None),
                    **event.model_dump(mode="json"),
                )
            elif hasattr(self, "_emit") and self._emit is not None:
                # Alternative: emit directly on action instance
                self._emit(event.event_name, **event.model_dump(mode="json"))
            else:
                # Fallback: store event for manual retrieval
                self._audit_event = event
                # Log that we couldn't publish
                logfire.debug(
                    "Audit event stored (no emitter available)",
                    action=event.action_name,
                    entity_type=event.entity_type,
                )
            
            return result
        
        # Store original run for introspection
        audited_run._original_run = original_run
        audited_run._audit_config = {
            "action": action,
            "entity_type": entity_type,
            "capture_input": capture_input,
            "capture_output": capture_output,
        }
        
        cls.run = audited_run
        return cls
    
    return decorator


# Re-export for backward compatibility
__all__ = ["audited"]


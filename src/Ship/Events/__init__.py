"""Ship-level domain events.

These events are used for cross-container communication
without creating direct dependencies between containers.
"""

from src.Ship.Events.ActionEvents import ActionExecuted

__all__ = ["ActionExecuted"]




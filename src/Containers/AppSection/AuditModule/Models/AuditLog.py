"""AuditLog model for storing audit trail."""

from piccolo.columns import JSONB, UUID, Text, Timestamptz, Varchar
from piccolo.columns.defaults.timestamptz import TimestamptzNow
from piccolo.columns.defaults.uuid import UUID4

from src.Ship.Parents.Model import Model


class AuditLog(Model):
    """Stores audit trail of all actions in the system.

    Attributes:
        id: Unique identifier
        actor_id: User who performed the action (null for system actions)
        actor_email: Email of the actor (denormalized for history)
        action: Action performed (e.g., "create", "update", "delete", "login")
        entity_type: Type of entity affected (e.g., "User", "Payment")
        entity_id: ID of the affected entity
        old_values: JSON of values before change
        new_values: JSON of values after change
        ip_address: IP address of the request
        user_agent: User agent string
        endpoint: API endpoint called
        http_method: HTTP method used
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        metadata: Additional context data
        created_at: When the action occurred
    """

    id = UUID(primary_key=True, default=UUID4())

    # Actor information
    actor_id = UUID(null=True, index=True)
    actor_email = Varchar(length=255, null=True)

    # Action details
    action = Varchar(length=50, required=True, index=True)
    entity_type = Varchar(length=100, null=True, index=True)
    entity_id = Varchar(length=255, null=True, index=True)

    # Change tracking
    old_values = JSONB(null=True)
    new_values = JSONB(null=True)

    # Request context
    ip_address = Varchar(length=45, null=True)  # IPv6 compatible
    user_agent = Text(null=True)
    endpoint = Varchar(length=500, null=True)
    http_method = Varchar(length=10, null=True)
    status_code = Varchar(length=3, null=True)
    duration_ms = Varchar(length=20, null=True)

    # Additional data
    metadata = JSONB(null=True)

    created_at = Timestamptz(default=TimestamptzNow(), index=True)

    class Meta:
        tablename = "audit_logs"

"""AuditModule errors."""

from typing import ClassVar
from uuid import UUID

from src.Ship.Core.Errors import BaseError, ErrorWithTemplate


class AuditError(BaseError):
    """Base error for AuditModule."""
    
    code: str = "AUDIT_ERROR"


class AuditLogNotFoundError(ErrorWithTemplate, AuditError):
    """Raised when audit log entry is not found."""
    
    _message_template: ClassVar[str] = "Audit log with id {audit_id} not found"
    code: str = "AUDIT_LOG_NOT_FOUND"
    http_status: int = 404
    audit_id: UUID


class InvalidAuditFilterError(ErrorWithTemplate, AuditError):
    """Raised when audit filter parameters are invalid."""
    
    _message_template: ClassVar[str] = "Invalid audit filter: {details}"
    code: str = "INVALID_AUDIT_FILTER"
    http_status: int = 400
    details: str




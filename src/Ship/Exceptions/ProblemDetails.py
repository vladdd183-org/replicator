"""Problem Details configuration (RFC 9457).

Provides standardized error responses according to RFC 9457.
All domain errors are automatically converted to Problem Details format.

Response format:
    {
        "type": "https://api.example.com/errors/user-not-found",
        "title": "User Not Found",
        "status": 404,
        "detail": "User with id 123 was not found",
        "instance": "/api/v1/users/123",
        "code": "USER_NOT_FOUND",  # Extension field
        ...extra fields from error
    }
"""

from typing import Any, Callable

from litestar.plugins.problem_details import (
    ProblemDetailsPlugin,
    ProblemDetailsConfig,
    ProblemDetailsException,
)
from pydantic import ValidationError

from src.Ship.Core.Errors import BaseError, DomainException  # Direct import to avoid circular
from src.Ship.Configs import get_settings


# Base URL for error type URIs
def _get_error_type_base() -> str:
    """Get base URL for error type URIs."""
    settings = get_settings()
    return f"https://api.{settings.app_name.lower().replace(' ', '-')}.com/errors"


def _code_to_type_uri(code: str) -> str:
    """Convert error code to type URI.
    
    Example: USER_NOT_FOUND -> https://api.hyper-porto-api.com/errors/user-not-found
    """
    slug = code.lower().replace("_", "-")
    return f"{_get_error_type_base()}/{slug}"


def _code_to_title(code: str) -> str:
    """Convert error code to human-readable title.
    
    Example: USER_NOT_FOUND -> User Not Found
    """
    return code.replace("_", " ").title()


def _error_to_problem_details(error: BaseError) -> ProblemDetailsException:
    """Convert BaseError to ProblemDetailsException.
    
    Extracts all error fields and includes them as extra data.
    """
    # Get all fields from the error model except base ones
    extra_fields: dict[str, Any] = {}
    for field_name, field_value in error.model_dump().items():
        if field_name not in ("message", "code", "http_status"):
            # Convert UUID to string for JSON serialization
            if hasattr(field_value, "hex"):
                extra_fields[field_name] = str(field_value)
            else:
                extra_fields[field_name] = field_value
    
    # Always include code as extension field
    extra_fields["code"] = error.code
    
    return ProblemDetailsException(
        type_=_code_to_type_uri(error.code),
        title=_code_to_title(error.code),
        status_code=error.http_status,
        detail=error.message,
        extra=extra_fields,
    )


def convert_domain_exception_to_problem_details(
    exc: DomainException,
) -> ProblemDetailsException:
    """Convert DomainException (wrapped BaseError) to ProblemDetailsException."""
    return _error_to_problem_details(exc.error)


def convert_base_error_to_problem_details(
    exc: BaseError,
) -> ProblemDetailsException:
    """Convert BaseError (and all subclasses) to ProblemDetailsException."""
    return _error_to_problem_details(exc)


def convert_pydantic_validation_error(
    exc: ValidationError,
) -> ProblemDetailsException:
    """Convert Pydantic ValidationError to ProblemDetailsException."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    return ProblemDetailsException(
        type_=f"{_get_error_type_base()}/validation-error",
        title="Validation Error",
        status_code=422,
        detail="Request validation failed",
        extra={
            "code": "VALIDATION_ERROR",
            "errors": errors,
        },
    )


def create_problem_details_plugin() -> ProblemDetailsPlugin:
    """Create and configure ProblemDetailsPlugin.
    
    Configures automatic conversion of:
    - DomainException (wrapper for BaseError)
    - Pydantic ValidationError
    - All HTTPExceptions
    """
    # Build exception mapping
    exception_map: dict[type[Exception], Callable[[Any], ProblemDetailsException]] = {
        DomainException: convert_domain_exception_to_problem_details,
        ValidationError: convert_pydantic_validation_error,
    }
    
    return ProblemDetailsPlugin(
        ProblemDetailsConfig(
            # Convert all HTTPExceptions to Problem Details
            enable_for_all_http_exceptions=True,
            # Map our custom exceptions
            exception_to_problem_detail_map=exception_map,
        )
    )


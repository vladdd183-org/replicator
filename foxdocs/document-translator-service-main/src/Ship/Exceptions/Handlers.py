"""Exception handlers."""

import logfire
from litestar import Request, Response
from litestar.exceptions import NotAuthorizedException

from src.Ship.Parents import PortoException


def exception_handler(request: Request, exc: PortoException) -> Response:
    """Handle Porto exceptions.

    Args:
        request: HTTP request
        exc: Porto exception

    Returns:
        HTTP response
    """
    logfire.error(
        f"🚨 Porto exception: {type(exc).__name__}",
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        exception_code=exc.code,
        request_path=request.url.path,
        request_method=request.method,
        status_code=exc.status_code,
        exc_info=True
    )

    return Response(
        content=exc.to_dict(),
        status_code=exc.status_code,
    )


def license_exception_handler(request: Request, exc: NotAuthorizedException) -> Response:
    """Handle license validation exceptions for HTTP requests.
    
    Automatically catches NotAuthorizedException thrown by Action.execute()
    and returns a proper HTTP 403 response.
    
    Args:
        request: HTTP request
        exc: NotAuthorizedException instance
        
    Returns:
        HTTP 403 response with license error details
    """
    logfire.warn(
        "🔐 License validation failed",
        request_path=request.url.path,
        request_method=request.method,
        client_ip=request.client.host if request.client else None,
        error_message=str(exc)
    )
    
    return Response(
        content={
            "status": "error",
            "error": "license_invalid",
            "message": str(exc),
            "status_code": 403
        },
        status_code=403,
    )

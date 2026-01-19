"""Base Controller class according to Porto architecture."""

import logfire
from abc import ABC
from typing import Any

from litestar import Controller as LitestarController
from litestar import Request


class Controller(ABC):
    """Base Controller class.

    Controllers are responsible for handling HTTP requests,
    validating input, calling actions, and returning responses.
    """

    def log_request(self, method: str, path: str, **kwargs) -> None:
        """Log incoming request.
        
        Args:
            method: HTTP method
            path: Request path
            **kwargs: Additional context
        """
        logfire.info(
            f"Incoming {method} request to {path}",
            method=method,
            path=path,
            controller=self.__class__.__name__,
            **kwargs
        )

    def log_response(self, status: int, **kwargs) -> None:
        """Log outgoing response.
        
        Args:
            status: HTTP status code
            **kwargs: Additional context
        """
        logfire.info(
            f"Response with status {status}",
            status_code=status,
            controller=self.__class__.__name__,
            **kwargs
        )


class BaseController(LitestarController):
    """Base Litestar controller with logging capabilities.
    
    This class combines Litestar's Controller with Porto's Controller patterns.
    """

    def log_request(self, request: Request, **kwargs) -> None:
        """Log incoming request.
        
        Args:
            request: Litestar request object
            **kwargs: Additional context
        """
        logfire.info(
            f"📥 {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            controller=self.__class__.__name__,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            **kwargs
        )

    def log_response(self, request: Request, status: int = 200, **kwargs) -> None:
        """Log outgoing response.
        
        Args:
            request: Litestar request object
            status: HTTP status code
            **kwargs: Additional context
        """
        status_emoji = "✅" if status < 400 else "❌"
        logfire.info(
            f"{status_emoji} {status} {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            status_code=status,
            controller=self.__class__.__name__,
            client_ip=request.client.host if request.client else None,
            **kwargs
        )

    def log_action_call(self, action_name: str, **kwargs) -> None:
        """Log action execution.
        
        Args:
            action_name: Name of the action being called
            **kwargs: Additional context
        """
        logfire.debug(
            f"🎯 Calling {action_name}",
            action=action_name,
            controller=self.__class__.__name__,
            **kwargs
        )

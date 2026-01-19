"""Logfire telemetry configuration.

Provides tracing and structured logging via Pydantic Logfire.
Integrates with Litestar for automatic request tracing.
"""

from typing import TYPE_CHECKING
from functools import wraps
from contextlib import contextmanager
import time

try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False

from src.Ship.Configs import get_settings

if TYPE_CHECKING:
    from litestar import Litestar

# Flag to track if logfire has been configured
_logfire_configured = False


def setup_logfire(app: "Litestar | None" = None) -> None:
    """Setup Logfire for tracing and logging.
    
    This function is idempotent - can be called multiple times safely.
    
    Args:
        app: Optional Litestar app for instrumentation
    """
    global _logfire_configured
    
    if not LOGFIRE_AVAILABLE:
        print("Logfire not installed, skipping telemetry setup")
        return
    
    settings = get_settings()
    
    # Configure Logfire only once
    if not _logfire_configured:
        logfire.configure(
            service_name=settings.app_name,
            service_version=settings.app_version,
            environment="development" if settings.is_development else "production",
            send_to_logfire=settings.is_production,  # Only send to cloud in production
            # In development, write to console without warnings
            console=logfire.ConsoleOptions(
                colors="auto",
                verbose=settings.app_debug,
            ) if settings.is_development else False,
        )
        _logfire_configured = True
        logfire.info("Logfire configured", app_name=settings.app_name, env=settings.app_env)
    
    # Instrument Litestar if provided
    if app is not None:
        try:
            from logfire.integrations.litestar import LogfirePlugin
            app.plugins.append(LogfirePlugin())
        except ImportError:
            pass


def ensure_logfire_configured() -> None:
    """Ensure logfire is configured before use.
    
    Call this at the start of any entry point (CLI, workers, etc.)
    that doesn't go through App.py.
    """
    if not _logfire_configured:
        setup_logfire()


def get_logger(name: str = __name__):
    """Get a structured logger.
    
    Args:
        name: Logger name (usually module name)
        
    Returns:
        Logfire logger or fallback print-based logger
    """
    if LOGFIRE_AVAILABLE:
        return logfire
    
    # Fallback logger using print
    class FallbackLogger:
        def __init__(self, name: str):
            self.name = name
        
        def info(self, message: str, **kwargs):
            print(f"[INFO] {self.name}: {message} {kwargs}")
        
        def warning(self, message: str, **kwargs):
            print(f"[WARNING] {self.name}: {message} {kwargs}")
        
        def error(self, message: str, **kwargs):
            print(f"[ERROR] {self.name}: {message} {kwargs}")
        
        def debug(self, message: str, **kwargs):
            print(f"[DEBUG] {self.name}: {message} {kwargs}")
        
        @contextmanager
        def span(self, name: str, **kwargs):
            start = time.time()
            try:
                yield
            finally:
                elapsed = time.time() - start
                print(f"[SPAN] {name}: {elapsed:.3f}s {kwargs}")
    
    return FallbackLogger(name)


# Global logger instance
logger = get_logger("app")


def traced(name: str | None = None):
    """Decorator to trace function execution.
    
    Args:
        name: Optional span name (defaults to function name)
        
    Example:
        @traced("create_user")
        async def run(self, data):
            ...
    """
    def decorator(func):
        span_name = name or func.__qualname__
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with logger.span(span_name):
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with logger.span(span_name):
                return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def log_action_result(action_name: str, result, duration_ms: float):
    """Log action execution result.
    
    Args:
        action_name: Name of the action
        result: Result object (Success or Failure)
        duration_ms: Execution duration in milliseconds
    """
    from returns.result import Success, Failure
    
    if isinstance(result, Success):
        logger.info(
            f"Action {action_name} succeeded",
            action=action_name,
            status="success",
            duration_ms=duration_ms,
        )
    elif isinstance(result, Failure):
        error = result.failure()
        logger.warning(
            f"Action {action_name} failed: {error}",
            action=action_name,
            status="failure",
            error=str(error),
            error_type=type(error).__name__,
            duration_ms=duration_ms,
        )


def log_request(method: str, path: str, status_code: int, duration_ms: float):
    """Log HTTP request.
    
    Args:
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
    """
    logger.info(
        f"{method} {path} -> {status_code}",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=duration_ms,
    )


def log_event(event_name: str, **data):
    """Log domain event.
    
    Args:
        event_name: Name of the event
        **data: Event data
    """
    logger.info(
        f"Event: {event_name}",
        event=event_name,
        **data,
    )


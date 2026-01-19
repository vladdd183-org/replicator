"""Authentication dependencies for Litestar.

Re-exports from Guards for backward compatibility with security.mdc.
"""

from src.Ship.Auth.Guards import auth_guard, optional_auth_guard

# Aliases for security.mdc compatibility
get_current_user = auth_guard
require_admin = auth_guard  # TODO: Implement proper admin check

__all__ = [
    "auth_guard",
    "optional_auth_guard",
    "get_current_user",
    "require_admin",
]

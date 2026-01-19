"""Licensing module for Document Translator Service."""

from .Middleware import check_license
from .helpers import execute_with_license_check

# Deprecated - use Action.execute() instead
from .Middleware import LicenseMiddleware
from .decorators import require_license, require_license_periodic, check_license_if_needed

__all__ = [
    # Recommended
    "execute_with_license_check",
    "check_license",
    # Deprecated
    "LicenseMiddleware",
    "require_license",
    "require_license_periodic", 
    "check_license_if_needed",
]


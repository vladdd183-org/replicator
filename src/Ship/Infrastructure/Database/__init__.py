"""Database infrastructure.

Re-exports DB engine from piccolo_conf.py (single source of truth).
"""

from piccolo_conf import DB

__all__ = ["DB"]

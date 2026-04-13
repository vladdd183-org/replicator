from __future__ import annotations

from src.Ship.Core.Errors import BaseError


class MemoryError(BaseError):
    code: str = "MEMORY_ERROR"


class MemoryNotFoundError(MemoryError):
    code: str = "MEMORY_NOT_FOUND"
    http_status: int = 404
    key: str = ""

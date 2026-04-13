from __future__ import annotations

from src.Ship.Core.Errors import BaseError


class RegistryError(BaseError):
    code: str = "REGISTRY_ERROR"


class CellNotFoundError(RegistryError):
    code: str = "CELL_NOT_FOUND"
    http_status: int = 404
    cell_name: str = ""


class CellAlreadyExistsError(RegistryError):
    code: str = "CELL_ALREADY_EXISTS"
    http_status: int = 409
    cell_name: str = ""

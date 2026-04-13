from __future__ import annotations

from src.Ship.Core.Errors import BaseError


class SpecError(BaseError):
    code: str = "SPEC_ERROR"
    http_status: int = 400


class SpecCompilationError(SpecError):
    code: str = "SPEC_COMPILATION_ERROR"
    intent: str = ""


class SpecValidationError(SpecError):
    code: str = "SPEC_VALIDATION_ERROR"
    field: str = ""
    reason: str = ""


class FormulaNotFoundError(SpecError):
    code: str = "FORMULA_NOT_FOUND"
    http_status: int = 404
    formula_name: str = ""

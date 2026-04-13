from __future__ import annotations

from src.Ship.Core.Errors import BaseError


class NixError(BaseError):
    code: str = "NIX_ERROR"


class NixBuildError(NixError):
    code: str = "NIX_BUILD_ERROR"
    flake_ref: str = ""


class NixEvalError(NixError):
    code: str = "NIX_EVAL_ERROR"
    expression: str = ""


class FlakeGenerationError(NixError):
    code: str = "FLAKE_GENERATION_ERROR"
    project_name: str = ""

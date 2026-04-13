from __future__ import annotations

from src.Ship.Core.Errors import BaseError


class TemplateError(BaseError):
    code: str = "TEMPLATE_ERROR"


class TemplateNotFoundError(TemplateError):
    code: str = "TEMPLATE_NOT_FOUND"
    http_status: int = 404
    template_name: str = ""


class TemplateRenderError(TemplateError):
    code: str = "TEMPLATE_RENDER_ERROR"
    template_name: str = ""
    reason: str = ""

from __future__ import annotations

from src.Ship.Core.Errors import BaseError


class EvolutionError(BaseError):
    code: str = "EVOLUTION_ERROR"


class VerificationFailedError(EvolutionError):
    code: str = "VERIFICATION_FAILED"
    check_type: str = ""
    details: str = ""


class PromotionDeniedError(EvolutionError):
    code: str = "PROMOTION_DENIED"
    http_status: int = 403
    reason: str = ""

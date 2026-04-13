from __future__ import annotations

from src.Ship.Core.Errors import BaseError


class BeadsError(BaseError):
    code: str = "BEADS_ERROR"


class BeadCreateError(BeadsError):
    code: str = "BEAD_CREATE_ERROR"


class BeadClaimError(BeadsError):
    code: str = "BEAD_CLAIM_ERROR"


class BeadCloseError(BeadsError):
    code: str = "BEAD_CLOSE_ERROR"

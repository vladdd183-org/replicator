# ruff: noqa: N999, I001
"""JWT-идентичность по IdentityPort (L0), обёртка над JWTService."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import jwt

from src.Ship.Adapters.Errors import IdentityVerificationError
from src.Ship.Adapters.Protocols import IdentityPort  # noqa: F401
from src.Ship.Auth.JWT import JWTService, get_jwt_service
from src.Ship.Core.Errors import DomainException
from src.Ship.Core.Types import Identity, ComputeResult, Capability  # noqa: F401


class JWTIdentityAdapter:
    """Выдача и проверка JWT; capabilities в extra_claims."""

    def __init__(self, jwt_service: JWTService | None = None) -> None:
        self._jwt = jwt_service or get_jwt_service()

    def _decode_verified(self, token: str) -> dict[str, Any]:
        if self._jwt.verify_token(token) is None:
            raise DomainException(
                IdentityVerificationError(message="Invalid or expired JWT token")
            )
        return jwt.decode(
            token,
            self._jwt.secret,
            algorithms=[self._jwt.algorithm],
        )

    async def verify(self, token: str) -> Identity:
        raw = self._decode_verified(token)
        caps = raw.get("capabilities", [])
        if not isinstance(caps, list):
            caps = []
        skip = frozenset({"sub", "capabilities", "exp", "iat"})
        return Identity(
            subject=str(raw.get("sub", "")),
            capabilities=[str(c) for c in caps],
            metadata={k: v for k, v in raw.items() if k not in skip},
        )

    async def issue(
        self,
        subject: str,
        capabilities: list[str],
        ttl_seconds: int = 3600,
    ) -> str:
        _ = ttl_seconds
        try:
            user_id = UUID(subject)
        except ValueError as e:
            raise DomainException(
                IdentityVerificationError(message="Subject must be a valid UUID string")
            ) from e
        return self._jwt.create_access_token(
            user_id,
            email=f"{user_id}@identity.local",
            extra_claims={"capabilities": capabilities},
        )

    async def delegate(self, parent_token: str, capabilities: list[str]) -> str:
        raw = self._decode_verified(parent_token)
        parent_caps = raw.get("capabilities", [])
        if not isinstance(parent_caps, list):
            parent_caps = []
        allowed = {str(c) for c in parent_caps}
        delegated = [c for c in capabilities if c in allowed]
        sub = raw.get("sub")
        if sub is None:
            raise DomainException(
                IdentityVerificationError(message="Parent token missing subject")
            )
        return await self.issue(str(sub), delegated)

    async def revoke(self, token: str) -> None:
        _ = token

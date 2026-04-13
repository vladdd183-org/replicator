"""Протоколы транспортного слоя L0: пять портов адаптеров Ship."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Protocol, runtime_checkable

from src.Ship.Core.Types import Identity, ComputeResult


@runtime_checkable
class StoragePort(Protocol):
    async def put(self, data: bytes, metadata: dict[str, Any] | None = None) -> str:
        ...

    async def get(self, identifier: str) -> bytes:
        ...

    async def exists(self, identifier: str) -> bool:
        ...

    async def delete(self, identifier: str) -> None:
        ...

    async def list_prefix(self, prefix: str) -> list[str]:
        ...


@runtime_checkable
class StatePort(Protocol):
    async def get(self, stream_id: str) -> dict[str, Any] | None:
        ...

    async def update(self, stream_id: str, patch: dict[str, Any]) -> str:
        ...

    async def create(self, schema: str, initial_data: dict[str, Any]) -> str:
        ...

    async def history(self, stream_id: str, limit: int = 100) -> list[dict[str, Any]]:
        ...


@runtime_checkable
class MessagingPort(Protocol):
    async def publish(
        self,
        topic: str,
        message: bytes,
        headers: dict[str, str] | None = None,
    ) -> None:
        ...

    async def subscribe(self, topic: str) -> AsyncIterator[tuple[bytes, dict[str, str]]]:
        ...

    async def request(self, topic: str, message: bytes, timeout: float = 5.0) -> bytes:
        ...


@runtime_checkable
class IdentityPort(Protocol):
    async def verify(self, token: str) -> Identity:
        ...

    async def issue(
        self,
        subject: str,
        capabilities: list[str],
        ttl_seconds: int = 3600,
    ) -> str:
        ...

    async def delegate(self, parent_token: str, capabilities: list[str]) -> str:
        ...

    async def revoke(self, token: str) -> None:
        ...


@runtime_checkable
class ComputePort(Protocol):
    async def execute(
        self,
        function_id: str,
        input_data: bytes,
        timeout_seconds: float = 60.0,
    ) -> ComputeResult:
        ...

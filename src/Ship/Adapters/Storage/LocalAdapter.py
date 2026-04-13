# ruff: noqa: N999, I001
"""Локальное файловое хранилище по StoragePort (L0)."""

from __future__ import annotations

import hashlib
from typing import Any

import anyio

from src.Ship.Adapters.Errors import StorageNotFoundError, StorageWriteError
from src.Ship.Adapters.Protocols import StoragePort  # noqa: F401
from src.Ship.Core.Errors import DomainException
from src.Ship.Core.Types import Identity, ComputeResult, Capability  # noqa: F401


class LocalStorageAdapter:
    """Файловое хранилище, шардирование по префиксу хеша (aa/остаток)."""

    def __init__(self, base_path: str | anyio.Path = "./data/storage/") -> None:
        self._base = anyio.Path(base_path) if isinstance(base_path, str) else base_path

    def _object_path(self, identifier: str) -> anyio.Path:
        if len(identifier) < 3:
            return self._base / identifier
        return self._base / identifier[:2] / identifier[2:]

    async def put(self, data: bytes, metadata: dict[str, Any] | None = None) -> str:
        _ = metadata
        digest = hashlib.sha256(data).hexdigest()
        target = self._object_path(digest)
        try:
            await target.parent.mkdir(parents=True, exist_ok=True)
            await target.write_bytes(data)
        except OSError as e:
            raise DomainException(
                StorageWriteError(message=f"Storage write failed: {e}")
            ) from e
        return digest

    async def get(self, identifier: str) -> bytes:
        path = self._object_path(identifier)
        if not await path.exists():
            raise DomainException(
                StorageNotFoundError(
                    message=f"Object not found: {identifier}",
                    identifier=identifier,
                )
            )
        try:
            return await path.read_bytes()
        except OSError as e:
            raise DomainException(
                StorageNotFoundError(
                    message=f"Object not found: {identifier}",
                    identifier=identifier,
                )
            ) from e

    async def exists(self, identifier: str) -> bool:
        return await self._object_path(identifier).is_file()

    async def delete(self, identifier: str) -> None:
        await self._object_path(identifier).unlink(missing_ok=True)

    async def list_prefix(self, prefix: str) -> list[str]:
        if not await self._base.exists():
            return []
        out: list[str] = []
        async for shard in self._base.iterdir():
            if not await shard.is_dir():
                continue
            async for f in shard.iterdir():
                if await f.is_file():
                    ident = shard.name + f.name
                    if ident.startswith(prefix):
                        out.append(ident)
        return sorted(out)

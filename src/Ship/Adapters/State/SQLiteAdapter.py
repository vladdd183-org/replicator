# ruff: noqa: N999, I001
"""Асинхронное SQLite-состояние по StatePort (L0)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import aiosqlite
import anyio

from src.Ship.Adapters.Errors import StateNotFoundError
from src.Ship.Adapters.Protocols import StatePort  # noqa: F401
from src.Ship.Core.Errors import DomainException
from src.Ship.Core.Types import Identity, ComputeResult, Capability  # noqa: F401

_SCHEMA = """
CREATE TABLE IF NOT EXISTS streams (
    stream_id TEXT PRIMARY KEY,
    schema TEXT NOT NULL,
    data TEXT NOT NULL,
    version INTEGER NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS stream_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_id TEXT NOT NULL,
    patch TEXT NOT NULL,
    version INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in patch.items():
        if (
            key in out
            and isinstance(out[key], dict)
            and isinstance(value, dict)
        ):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


class SQLiteStateAdapter:
    """Версионируемые JSON-streams в SQLite."""

    def __init__(self, db_path: str = "./data/state.db") -> None:
        if db_path == ":memory:":
            self._db_path = "file::memory:?cache=shared"
            self._db_uri = True
        else:
            self._db_path = db_path
            self._db_uri = False
        self._lock = anyio.Lock()
        self._conn: aiosqlite.Connection | None = None

    async def _ensure_conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            self._conn = await aiosqlite.connect(self._db_path, uri=self._db_uri)
            await self._conn.executescript(_SCHEMA)
            await self._conn.commit()
        return self._conn

    async def create(self, schema: str, initial_data: dict[str, Any]) -> str:
        stream_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        payload = json.dumps(initial_data)
        async with self._lock:
            db = await self._ensure_conn()
            await db.execute(
                "INSERT INTO streams (stream_id, schema, data, version, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (stream_id, schema, payload, 1, now),
            )
            await db.commit()
        return stream_id

    async def get(self, stream_id: str) -> dict[str, Any] | None:
        async with self._lock:
            db = await self._ensure_conn()
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT data FROM streams WHERE stream_id = ?",
                (stream_id,),
            )
            row = await cur.fetchone()
        if row is None:
            return None
        return json.loads(row["data"])

    async def update(self, stream_id: str, patch: dict[str, Any]) -> str:
        now = datetime.now(UTC).isoformat()
        async with self._lock:
            db = await self._ensure_conn()
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT data, version FROM streams WHERE stream_id = ?",
                (stream_id,),
            )
            row = await cur.fetchone()
            if row is None:
                raise DomainException(
                    StateNotFoundError(
                        message=f"Stream not found: {stream_id}",
                        stream_id=stream_id,
                    )
                )
            current = json.loads(row["data"])
            version = int(row["version"])
            merged = _deep_merge(current, patch)
            new_version = version + 1
            await db.execute(
                "UPDATE streams SET data = ?, version = ?, updated_at = ? "
                "WHERE stream_id = ?",
                (json.dumps(merged), new_version, now, stream_id),
            )
            await db.execute(
                "INSERT INTO stream_history (stream_id, patch, version, created_at) "
                "VALUES (?, ?, ?, ?)",
                (stream_id, json.dumps(patch), new_version, now),
            )
            await db.commit()
        return str(new_version)

    async def history(self, stream_id: str, limit: int = 100) -> list[dict[str, Any]]:
        async with self._lock:
            db = await self._ensure_conn()
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT stream_id, patch, version, created_at "
                "FROM stream_history WHERE stream_id = ? "
                "ORDER BY version ASC LIMIT ?",
                (stream_id, limit),
            )
            rows = await cur.fetchall()
        return [
            {
                "stream_id": r["stream_id"],
                "patch": json.loads(r["patch"]),
                "version": int(r["version"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]

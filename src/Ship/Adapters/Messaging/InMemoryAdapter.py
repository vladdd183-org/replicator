# ruff: noqa: N999, I001
"""In-memory pub/sub по MessagingPort (L0)."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator

import anyio

from src.Ship.Adapters.Errors import MessagingTimeoutError
from src.Ship.Adapters.Protocols import MessagingPort  # noqa: F401
from src.Ship.Core.Errors import DomainException
from src.Ship.Core.Types import Identity, ComputeResult, Capability  # noqa: F401


class InMemoryMessagingAdapter:
    """Топики: fan-out в несколько asyncio.Queue."""

    def __init__(self) -> None:
        self._topics: dict[str, list[asyncio.Queue[tuple[bytes, dict[str, str]]]]] = {}

    async def publish(
        self,
        topic: str,
        message: bytes,
        headers: dict[str, str] | None = None,
    ) -> None:
        hdrs = dict(headers or {})
        for q in self._topics.get(topic, []):
            await q.put((message, hdrs))

    async def subscribe(self, topic: str) -> AsyncIterator[tuple[bytes, dict[str, str]]]:
        async def _messages() -> AsyncIterator[tuple[bytes, dict[str, str]]]:
            q: asyncio.Queue[tuple[bytes, dict[str, str]]] = asyncio.Queue()
            self._topics.setdefault(topic, []).append(q)
            try:
                while True:
                    yield await q.get()
            finally:
                subs = self._topics.get(topic, [])
                if q in subs:
                    subs.remove(q)
                if not subs and topic in self._topics:
                    del self._topics[topic]

        async for item in _messages():
            yield item

    async def request(self, topic: str, message: bytes, timeout: float = 5.0) -> bytes:
        reply_topic = f"_reply.{uuid.uuid4().hex}"
        q: asyncio.Queue[tuple[bytes, dict[str, str]]] = asyncio.Queue(maxsize=1)
        self._topics.setdefault(reply_topic, []).append(q)
        try:
            await self.publish(
                topic,
                message,
                headers={"reply_to": reply_topic},
            )
            try:
                with anyio.fail_after(timeout):
                    msg, _ = await q.get()
                    return msg
            except TimeoutError:
                raise DomainException(
                    MessagingTimeoutError(
                        message=f"Messaging request timeout on topic {topic!r}",
                        topic=topic,
                        timeout_seconds=timeout,
                    )
                ) from None
        finally:
            subs = self._topics.get(reply_topic, [])
            if q in subs:
                subs.remove(q)
            if not subs and reply_topic in self._topics:
                del self._topics[reply_topic]

from __future__ import annotations

from src.Ship.Parents.Event import DomainEvent


class ToolCalled(DomainEvent):
    server: str
    tool_name: str
    success: bool = True


class ServerConnected(DomainEvent):
    server: str

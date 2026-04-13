from __future__ import annotations

from dishka import Provider, Scope, provide

from src.Containers.ToolSection.MCPClientModule.Actions.CallToolAction import (
    CallToolAction,
)


class MCPClientModuleProvider(Provider):
    scope = Scope.REQUEST

    call_tool = provide(CallToolAction)

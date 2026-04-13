from __future__ import annotations

from typing import Any

from dishka import Provider, Scope, provide

from src.Containers.AgentSection.CompassModule.Actions.StrategizeAction import (
    StrategizeAction,
)


class CompassModuleProvider(Provider):
    """DI-провайдер для CompassModule."""

    scope = Scope.REQUEST

    @provide
    def strategize_action(self, llm_client: Any = None) -> StrategizeAction:
        return StrategizeAction(llm_client=llm_client)

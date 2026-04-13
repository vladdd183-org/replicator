from __future__ import annotations

from typing import Any

from dishka import Provider, Scope, provide

from src.Containers.AgentSection.MakerModule.Actions.DecomposeAction import (
    DecomposeAction,
)
from src.Containers.AgentSection.MakerModule.Actions.VoteAction import VoteAction


class MakerModuleProvider(Provider):
    """DI-провайдер для MakerModule."""

    scope = Scope.REQUEST

    @provide
    def decompose_action(self, llm_client: Any = None) -> DecomposeAction:
        return DecomposeAction(llm_client=llm_client)

    @provide
    def vote_action(self, llm_client: Any = None) -> VoteAction:
        return VoteAction(llm_client=llm_client)

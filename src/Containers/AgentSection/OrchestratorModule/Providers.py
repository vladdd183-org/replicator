from __future__ import annotations

from typing import Any

from dishka import Provider, Scope, provide

from src.Containers.AgentSection.OrchestratorModule.Actions.ExecuteBeadAction import (
    ExecuteBeadAction,
)
from src.Containers.AgentSection.OrchestratorModule.Actions.ExecuteBeadGraphAction import (
    ExecuteBeadGraphAction,
)


class OrchestratorModuleProvider(Provider):
    """DI-провайдер для OrchestratorModule."""

    scope = Scope.REQUEST

    @provide
    def execute_bead_action(
        self, llm_client: Any = None, compute_port: Any = None,
    ) -> ExecuteBeadAction:
        return ExecuteBeadAction(llm_client=llm_client, compute_port=compute_port)

    @provide
    def execute_bead_graph_action(
        self, llm_client: Any = None, compute_port: Any = None,
    ) -> ExecuteBeadGraphAction:
        return ExecuteBeadGraphAction(llm_client=llm_client, compute_port=compute_port)

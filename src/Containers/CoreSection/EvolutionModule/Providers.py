from __future__ import annotations

from dishka import Provider, Scope, provide

from src.Containers.CoreSection.EvolutionModule.Actions.PromoteAction import (
    PromoteAction,
)
from src.Containers.CoreSection.EvolutionModule.Actions.VerifyAction import (
    VerifyAction,
)


class EvolutionModuleProvider(Provider):
    scope = Scope.REQUEST

    verify = provide(VerifyAction)
    promote = provide(PromoteAction)

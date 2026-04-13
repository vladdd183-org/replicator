from __future__ import annotations

from dishka import Provider, Scope, provide

from src.Containers.ToolSection.NixModule.Actions.BuildAction import BuildAction
from src.Containers.ToolSection.NixModule.Actions.GenerateFlakeAction import (
    GenerateFlakeAction,
)


class NixModuleProvider(Provider):
    scope = Scope.REQUEST

    build = provide(BuildAction)
    generate_flake = provide(GenerateFlakeAction)

from __future__ import annotations

from dishka import Provider, Scope, provide

from src.Containers.CoreSection.TemplateModule.Actions.GenerateModuleAction import (
    GenerateModuleAction,
)


class TemplateModuleProvider(Provider):
    scope = Scope.REQUEST

    generate_module = provide(GenerateModuleAction)

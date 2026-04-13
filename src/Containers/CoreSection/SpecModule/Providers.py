from __future__ import annotations

from dishka import Provider, Scope, provide

from src.Containers.CoreSection.SpecModule.Actions.CompileSpecAction import (
    CompileSpecAction,
)
from src.Containers.CoreSection.SpecModule.Actions.ValidateSpecAction import (
    ValidateSpecAction,
)


class SpecModuleProvider(Provider):
    scope = Scope.REQUEST

    compile_spec = provide(CompileSpecAction)
    validate_spec = provide(ValidateSpecAction)

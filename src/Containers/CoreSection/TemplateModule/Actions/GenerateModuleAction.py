from __future__ import annotations

from pydantic import BaseModel, Field
from returns.result import Failure, Result, Success

from src.Containers.CoreSection.TemplateModule.Errors import TemplateRenderError
from src.Ship.Parents.Action import Action


class ModuleConfig(BaseModel):
    model_config = {"frozen": True}

    section: str
    module_name: str
    with_actions: list[str] = Field(default_factory=list)
    with_tasks: list[str] = Field(default_factory=list)
    with_queries: list[str] = Field(default_factory=list)


class GenerateModuleAction(
    Action[ModuleConfig, dict[str, str], TemplateRenderError],
):
    """Генерирует файловую структуру Porto-модуля."""

    async def run(
        self, data: ModuleConfig,
    ) -> Result[dict[str, str], TemplateRenderError]:
        try:
            files = self._generate(data)
            return Success(files)
        except Exception as e:
            return Failure(TemplateRenderError(
                message=f"Failed to generate module: {e}",
                template_name="porto_module",
                reason=str(e),
            ))

    def _generate(self, cfg: ModuleConfig) -> dict[str, str]:
        base = f"src/Containers/{cfg.section}/{cfg.module_name}"
        files: dict[str, str] = {}

        files[f"{base}/__init__.py"] = ""
        files[f"{base}/Actions/__init__.py"] = ""
        files[f"{base}/Data/__init__.py"] = ""
        files[f"{base}/Data/Schemas/__init__.py"] = ""

        files[f"{base}/Errors.py"] = self._render_errors(cfg.module_name)
        files[f"{base}/Events.py"] = self._render_events(cfg.module_name)
        files[f"{base}/Providers.py"] = self._render_providers(cfg)

        for action_name in cfg.with_actions:
            files[f"{base}/Actions/{action_name}.py"] = self._render_action(
                cfg, action_name,
            )

        return files

    def _render_errors(self, module_name: str) -> str:
        base_error = module_name.replace("Module", "Error")
        return (
            "from __future__ import annotations\n\n"
            "from src.Ship.Core.Errors import BaseError\n\n\n"
            f"class {base_error}(BaseError):\n"
            f'    code: str = "{base_error.upper()}"\n'
        )

    def _render_events(self, module_name: str) -> str:
        return (
            "from __future__ import annotations\n\n"
            "from src.Ship.Parents.Event import DomainEvent\n\n\n"
            f"# Определите события для {module_name}\n"
        )

    def _render_providers(self, cfg: ModuleConfig) -> str:
        lines = [
            "from __future__ import annotations\n",
            "",
            "from dishka import Provider, Scope, provide",
            "",
        ]
        imports = []
        provides = []
        for action_name in cfg.with_actions:
            import_path = (
                f"src.Containers.{cfg.section}.{cfg.module_name}"
                f".Actions.{action_name}"
            )
            imports.append(f"from {import_path} import {action_name}")
            attr_name = self._to_snake_case(action_name)
            provides.append(f"    {attr_name} = provide({action_name})")

        for imp in imports:
            lines.append(imp)
        lines.append("")
        lines.append("")
        provider_name = cfg.module_name.replace("Module", "ModuleProvider")
        lines.append(f"class {provider_name}(Provider):")
        lines.append("    scope = Scope.REQUEST")
        if provides:
            lines.append("")
            lines.extend(provides)
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _to_snake_case(name: str) -> str:
        result: list[str] = []
        for i, ch in enumerate(name):
            if ch.isupper() and i > 0:
                result.append("_")
            result.append(ch.lower())
        return "".join(result)

    def _render_action(self, cfg: ModuleConfig, action_name: str) -> str:
        module_error = cfg.module_name.replace("Module", "Error")
        import_path = (
            f"src.Containers.{cfg.section}.{cfg.module_name}.Errors"
        )
        return (
            "from __future__ import annotations\n\n"
            "from returns.result import Result, Success\n\n"
            f"from {import_path} import {module_error}\n"
            "from src.Ship.Parents.Action import Action\n\n\n"
            f"class {action_name}(Action[str, str, {module_error}]):\n"
            f'    """TODO: реализовать {action_name}."""\n\n'
            f"    async def run(self, data: str) -> Result[str, {module_error}]:\n"
            '        return Success("ok")\n'
        )

from __future__ import annotations

from textwrap import dedent

from pydantic import BaseModel
from returns.result import Failure, Result, Success

from src.Containers.ToolSection.NixModule.Errors import FlakeGenerationError, NixError
from src.Ship.Parents.Action import Action


class FlakeConfig(BaseModel):
    model_config = {"frozen": True}

    project_name: str
    python_version: str = "3.13"
    description: str = ""


_FLAKE_TEMPLATE = dedent("""\
    {{
      description = "{description}";

      inputs = {{
        nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
        flake-utils.url = "github:numtide/flake-utils";
      }};

      outputs = {{ self, nixpkgs, flake-utils }}:
        flake-utils.lib.eachDefaultSystem (system:
          let
            pkgs = nixpkgs.legacyPackages.${{system}};
            python = pkgs.{python_pkg};
          in {{
            devShells.default = pkgs.mkShell {{
              name = "{project_name}-dev";
              packages = [
                python
                pkgs.uv
              ];
              shellHook = ''
                echo "{project_name} dev shell activated (Python {python_version})"
              '';
            }};
          }}
        );
    }}
""")

_PYTHON_PKG_MAP: dict[str, str] = {
    "3.11": "python311",
    "3.12": "python312",
    "3.13": "python313",
}


class GenerateFlakeAction(Action[FlakeConfig, str, NixError]):
    """Генерация flake.nix по конфигурации проекта."""

    async def run(self, data: FlakeConfig) -> Result[str, NixError]:
        try:
            python_pkg = _PYTHON_PKG_MAP.get(
                data.python_version,
                f"python{data.python_version.replace('.', '')}",
            )

            description = data.description or f"{data.project_name} project"

            content = _FLAKE_TEMPLATE.format(
                description=description,
                python_pkg=python_pkg,
                project_name=data.project_name,
                python_version=data.python_version,
            )

            return Success(content)

        except Exception as e:
            return Failure(FlakeGenerationError(
                message=f"Flake generation error: {e}",
                project_name=data.project_name,
            ))

from __future__ import annotations

import shutil

import anyio
from pydantic import BaseModel
from returns.result import Failure, Result, Success

from src.Containers.ToolSection.NixModule.Errors import NixBuildError, NixError
from src.Ship.Parents.Action import Action


class BuildRequest(BaseModel):
    model_config = {"frozen": True}

    flake_ref: str
    output: str = "result"


class BuildAction(Action[BuildRequest, str, NixError]):
    """Запуск nix build для flake-ссылки."""

    async def run(self, data: BuildRequest) -> Result[str, NixError]:
        if not shutil.which("nix"):
            return Failure(NixBuildError(
                message="nix not found in PATH; install Nix first",
                flake_ref=data.flake_ref,
            ))

        try:
            target = f"{data.flake_ref}#{data.output}" if "#" not in data.flake_ref else data.flake_ref

            result = await anyio.run_process(
                ["nix", "build", target, "--no-link", "--print-out-paths"],
                check=False,
            )

            if result.returncode != 0:
                stderr = result.stderr.decode()[:500]
                return Failure(NixBuildError(
                    message=f"nix build failed: {stderr}",
                    flake_ref=data.flake_ref,
                ))

            output_path = result.stdout.decode().strip()
            return Success(output_path)

        except Exception as e:
            return Failure(NixBuildError(
                message=f"Build error: {e}",
                flake_ref=data.flake_ref,
            ))

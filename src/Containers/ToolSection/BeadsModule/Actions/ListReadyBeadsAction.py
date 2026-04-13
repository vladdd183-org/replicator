from __future__ import annotations

import json
from typing import Any

import anyio
from returns.result import Result, Success

from src.Ship.Parents.Action import Action
from src.Containers.ToolSection.BeadsModule.Errors import BeadsError

BD_CMD = "/home/vladdd183/.local/bin/bd-wrapper"


class ListReadyBeadsAction(Action[None, list[dict[str, Any]], BeadsError]):
    def __init__(self, project_root: str = ".") -> None:
        self._root = project_root

    async def run(self, data: None = None) -> Result[list[dict[str, Any]], BeadsError]:
        try:
            cmd = [BD_CMD, "ready", "--json"]
            result = await anyio.run_process(cmd, cwd=self._root, check=False)

            if result.returncode != 0:
                return Success([])

            parsed = json.loads(result.stdout.decode())
            if isinstance(parsed, list):
                return Success(parsed)
            return Success([parsed])
        except Exception:
            return Success([])

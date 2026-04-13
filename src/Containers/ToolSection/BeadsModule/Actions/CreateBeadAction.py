from __future__ import annotations

import json
from typing import Any

import anyio
from pydantic import BaseModel
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.ToolSection.BeadsModule.Errors import BeadsError, BeadCreateError

BD_CMD = "/home/vladdd183/.local/bin/bd-wrapper"


class CreateBeadRequest(BaseModel):
    model_config = {"frozen": True}
    title: str
    description: str = ""
    priority: int = 1
    issue_type: str = "task"


class CreateBeadAction(Action[CreateBeadRequest, dict[str, Any], BeadsError]):
    def __init__(self, project_root: str = ".") -> None:
        self._root = project_root

    async def run(self, data: CreateBeadRequest) -> Result[dict[str, Any], BeadsError]:
        try:
            cmd = [BD_CMD, "create", data.title, "-p", str(data.priority), "-t", data.issue_type, "--json"]
            result = await anyio.run_process(cmd, cwd=self._root, check=False)

            if result.returncode != 0:
                return Failure(BeadCreateError(
                    message=f"bd create failed: {result.stderr.decode()[:500]}",
                ))

            parsed = json.loads(result.stdout.decode())
            return Success(parsed)
        except Exception as e:
            return Failure(BeadCreateError(message=f"Failed to create bead: {e}"))

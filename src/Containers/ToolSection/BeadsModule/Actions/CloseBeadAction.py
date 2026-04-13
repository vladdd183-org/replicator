from __future__ import annotations

import json
from typing import Any

import anyio
from pydantic import BaseModel
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.ToolSection.BeadsModule.Errors import BeadsError, BeadCloseError

BD_CMD = "/home/vladdd183/.local/bin/bd-wrapper"


class CloseBeadRequest(BaseModel):
    model_config = {"frozen": True}
    bead_id: str
    reason: str = "Completed"


class CloseBeadAction(Action[CloseBeadRequest, dict[str, Any], BeadsError]):
    def __init__(self, project_root: str = ".") -> None:
        self._root = project_root

    async def run(self, data: CloseBeadRequest) -> Result[dict[str, Any], BeadsError]:
        try:
            cmd = [BD_CMD, "close", data.bead_id, "--reason", data.reason, "--json"]
            result = await anyio.run_process(cmd, cwd=self._root, check=False)

            if result.returncode != 0:
                return Failure(BeadCloseError(
                    message=f"bd close failed: {result.stderr.decode()[:500]}",
                ))

            parsed = json.loads(result.stdout.decode())
            return Success(parsed)
        except Exception as e:
            return Failure(BeadCloseError(message=f"Failed to close bead: {e}"))

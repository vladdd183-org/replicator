from __future__ import annotations

import anyio
from pydantic import BaseModel
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.ToolSection.BeadsModule.Errors import BeadsError

BD_CMD = "/home/vladdd183/.local/bin/bd-wrapper"


class AddDepRequest(BaseModel):
    model_config = {"frozen": True}
    child_id: str
    parent_id: str


class AddDependencyAction(Action[AddDepRequest, bool, BeadsError]):
    def __init__(self, project_root: str = ".") -> None:
        self._root = project_root

    async def run(self, data: AddDepRequest) -> Result[bool, BeadsError]:
        try:
            cmd = [BD_CMD, "dep", "add", data.child_id, data.parent_id]
            result = await anyio.run_process(cmd, cwd=self._root, check=False)
            return Success(result.returncode == 0)
        except Exception as e:
            return Failure(BeadsError(message=f"Failed to add dependency: {e}"))

from __future__ import annotations

import json
from typing import Any

import anyio
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.ToolSection.BeadsModule.Errors import BeadsError, BeadClaimError

BD_CMD = "/home/vladdd183/.local/bin/bd-wrapper"


class ClaimBeadAction(Action[str, dict[str, Any], BeadsError]):
    def __init__(self, project_root: str = ".") -> None:
        self._root = project_root

    async def run(self, data: str) -> Result[dict[str, Any], BeadsError]:
        try:
            cmd = [BD_CMD, "update", data, "--claim", "--json"]
            result = await anyio.run_process(cmd, cwd=self._root, check=False)

            if result.returncode != 0:
                return Failure(BeadClaimError(
                    message=f"bd claim failed: {result.stderr.decode()[:500]}",
                ))

            parsed = json.loads(result.stdout.decode())
            return Success(parsed)
        except Exception as e:
            return Failure(BeadClaimError(message=f"Failed to claim bead: {e}"))

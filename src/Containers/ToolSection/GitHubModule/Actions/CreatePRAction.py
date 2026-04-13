from __future__ import annotations

import json
from typing import Any

import anyio
from pydantic import BaseModel
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.ToolSection.GitHubModule.Errors import GitHubError, PRCreateError


class CreatePRRequest(BaseModel):
    model_config = {"frozen": True}
    title: str
    body: str = ""
    base: str = "main"
    draft: bool = False


class CreatePRAction(Action[CreatePRRequest, dict[str, Any], GitHubError]):
    def __init__(self, project_root: str = ".") -> None:
        self._root = project_root

    async def run(self, data: CreatePRRequest) -> Result[dict[str, Any], GitHubError]:
        try:
            cmd = [
                "gh", "pr", "create",
                "--title", data.title,
                "--body", data.body,
                "--base", data.base,
                "--json", "number,url,title,state",
            ]
            if data.draft:
                cmd.append("--draft")

            result = await anyio.run_process(cmd, cwd=self._root, check=False)

            if result.returncode != 0:
                stderr = result.stderr.decode()[:500]
                return Failure(PRCreateError(message=f"gh pr create failed: {stderr}"))

            parsed = json.loads(result.stdout.decode())
            return Success(parsed)
        except Exception as e:
            return Failure(PRCreateError(message=f"Failed to create PR: {e}"))

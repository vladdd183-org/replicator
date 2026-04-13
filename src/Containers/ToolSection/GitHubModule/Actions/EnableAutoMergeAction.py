from __future__ import annotations

import anyio
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.ToolSection.GitHubModule.Errors import GitHubError, PRMergeError


class EnableAutoMergeAction(Action[int, bool, GitHubError]):
    def __init__(self, project_root: str = ".") -> None:
        self._root = project_root

    async def run(self, data: int) -> Result[bool, GitHubError]:
        try:
            cmd = ["gh", "pr", "merge", str(data), "--auto", "--squash"]
            result = await anyio.run_process(cmd, cwd=self._root, check=False)

            if result.returncode != 0:
                stderr = result.stderr.decode()[:500]
                return Failure(PRMergeError(message=f"gh pr merge --auto failed: {stderr}"))

            return Success(True)
        except Exception as e:
            return Failure(PRMergeError(message=f"Failed to enable auto-merge: {e}"))

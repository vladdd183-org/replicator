from __future__ import annotations

import anyio
from pydantic import BaseModel
from returns.result import Failure, Result, Success

from src.Containers.ToolSection.GitModule.Errors import GitCloneError, GitError
from src.Ship.Parents.Action import Action


class CloneRequest(BaseModel):
    model_config = {"frozen": True}

    url: str
    path: str
    branch: str | None = None


class CloneRepoAction(Action[CloneRequest, str, GitError]):
    """Клонирование git-репозитория."""

    async def run(self, data: CloneRequest) -> Result[str, GitError]:
        try:
            cmd = ["git", "clone"]
            if data.branch:
                cmd.extend(["--branch", data.branch])
            cmd.extend([data.url, data.path])

            result = await anyio.run_process(cmd, check=False)

            if result.returncode != 0:
                stderr = result.stderr.decode()[:500]
                return Failure(GitCloneError(
                    message=f"Clone failed: {stderr}",
                    url=data.url,
                ))

            return Success(data.path)

        except Exception as e:
            return Failure(GitCloneError(
                message=f"Clone error: {e}",
                url=data.url,
            ))

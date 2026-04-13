from __future__ import annotations

import anyio
from pydantic import BaseModel
from returns.result import Failure, Result, Success

from src.Containers.ToolSection.GitModule.Errors import GitError
from src.Ship.Parents.Action import Action


class CreateBranchRequest(BaseModel):
    model_config = {"frozen": True}

    repo_path: str
    branch_name: str
    base_branch: str = "main"


class CreateBranchAction(Action[CreateBranchRequest, str, GitError]):
    """Создание новой git-ветки."""

    async def run(self, data: CreateBranchRequest) -> Result[str, GitError]:
        try:
            result = await anyio.run_process(
                ["git", "checkout", "-b", data.branch_name, data.base_branch],
                cwd=data.repo_path,
                check=False,
            )

            if result.returncode != 0:
                stderr = result.stderr.decode()[:500]
                return Failure(GitError(
                    message=f"Branch creation failed: {stderr}",
                ))

            return Success(data.branch_name)

        except Exception as e:
            return Failure(GitError(
                message=f"Branch creation error: {e}",
            ))

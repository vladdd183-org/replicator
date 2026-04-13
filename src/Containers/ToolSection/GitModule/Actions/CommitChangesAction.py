from __future__ import annotations

import anyio
from pydantic import BaseModel, Field
from returns.result import Failure, Result, Success

from src.Containers.ToolSection.GitModule.Errors import GitError
from src.Ship.Parents.Action import Action


class CommitRequest(BaseModel):
    model_config = {"frozen": True}

    repo_path: str
    message: str
    files: list[str] = Field(default_factory=list)
    all_changes: bool = False


class CommitChangesAction(Action[CommitRequest, str, GitError]):
    """Стейджинг файлов и создание git-коммита."""

    async def run(self, data: CommitRequest) -> Result[str, GitError]:
        try:
            if data.all_changes:
                add_result = await anyio.run_process(
                    ["git", "add", "-A"],
                    cwd=data.repo_path,
                    check=False,
                )
            elif data.files:
                add_result = await anyio.run_process(
                    ["git", "add", *data.files],
                    cwd=data.repo_path,
                    check=False,
                )
            else:
                return Failure(GitError(
                    message="No files specified and all_changes is False",
                ))

            if add_result.returncode != 0:
                stderr = add_result.stderr.decode()[:500]
                return Failure(GitError(
                    message=f"Git add failed: {stderr}",
                ))

            commit_result = await anyio.run_process(
                ["git", "commit", "-m", data.message],
                cwd=data.repo_path,
                check=False,
            )

            if commit_result.returncode != 0:
                stderr = commit_result.stderr.decode()[:500]
                return Failure(GitError(
                    message=f"Git commit failed: {stderr}",
                ))

            hash_result = await anyio.run_process(
                ["git", "rev-parse", "HEAD"],
                cwd=data.repo_path,
                check=False,
            )

            commit_hash = hash_result.stdout.decode().strip()
            return Success(commit_hash)

        except Exception as e:
            return Failure(GitError(
                message=f"Commit error: {e}",
            ))

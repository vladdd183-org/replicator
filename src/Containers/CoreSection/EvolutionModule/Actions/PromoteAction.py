from __future__ import annotations

import asyncio
from dataclasses import dataclass

from returns.result import Failure, Result, Success

from src.Containers.CoreSection.EvolutionModule.Errors import (
    EvolutionError,
    PromotionDeniedError,
)
from src.Containers.CoreSection.SpecModule.Data.Schemas.Models import EvidenceBundle
from src.Ship.Parents.Action import Action


@dataclass(frozen=True)
class PromotionInput:
    evidence: EvidenceBundle
    intent_type: str
    commit_message: str = "chore: auto-promote verified changes"


class PromoteAction(Action[PromotionInput, str, EvolutionError]):
    """Промоутит верифицированные изменения (git commit / создание структуры)."""

    def __init__(self, project_root: str = ".") -> None:
        self._root = project_root

    async def run(self, data: PromotionInput) -> Result[str, EvolutionError]:
        if data.evidence.status != "pass":
            return Failure(PromotionDeniedError(
                message="Cannot promote: verification did not pass",
                reason=f"Evidence status: {data.evidence.status}",
            ))

        if data.intent_type == "self_evolve":
            return await self._promote_self_evolve(data)
        if data.intent_type == "generate":
            return await self._promote_generate(data)
        return await self._promote_legacy(data)

    async def _promote_self_evolve(
        self, data: PromotionInput,
    ) -> Result[str, EvolutionError]:
        """Self-evolve: git add + commit."""
        add_result = await self._git("add", "-A")
        if add_result.returncode != 0:
            return Failure(PromotionDeniedError(
                message=f"git add failed: {add_result.stderr}",
                reason="git_add_failed",
            ))

        commit_result = await self._git("commit", "-m", data.commit_message)
        if commit_result.returncode != 0:
            if "nothing to commit" in commit_result.stdout:
                return Success("No changes to commit")
            return Failure(PromotionDeniedError(
                message=f"git commit failed: {commit_result.stderr}",
                reason="git_commit_failed",
            ))

        return Success(f"Committed: {data.commit_message}")

    async def _promote_generate(
        self, data: PromotionInput,
    ) -> Result[str, EvolutionError]:
        """Generate: подтверждаем создание структуры."""
        return Success(
            f"Generated project verified and ready "
            f"({len(data.evidence.test_results)} checks)",
        )

    async def _promote_legacy(
        self, data: PromotionInput,
    ) -> Result[str, EvolutionError]:
        """Legacy: git add + commit, аналогично self_evolve."""
        return await self._promote_self_evolve(data)

    async def _git(self, *args: str) -> _ProcessResult:
        proc = await asyncio.create_subprocess_exec(
            "git", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self._root,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
        return _ProcessResult(
            returncode=proc.returncode or 0,
            stdout=stdout_bytes.decode(errors="replace"),
            stderr=stderr_bytes.decode(errors="replace"),
        )


@dataclass(frozen=True)
class _ProcessResult:
    returncode: int
    stdout: str
    stderr: str

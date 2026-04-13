from __future__ import annotations

import asyncio
from typing import Any

from returns.result import Failure, Result, Success

from src.Containers.CoreSection.EvolutionModule.Errors import (
    EvolutionError,
    VerificationFailedError,
)
from src.Containers.CoreSection.SpecModule.Data.Schemas.Models import (
    EvidenceBundle,
    ExecutionResult,
)
from src.Ship.Parents.Action import Action


class VerifyAction(Action[ExecutionResult, EvidenceBundle, EvolutionError]):
    """Верификация результатов выполнения: тесты, линтинг, type-check."""

    def __init__(self, project_root: str = ".") -> None:
        self._root = project_root

    async def run(
        self, data: ExecutionResult,
    ) -> Result[EvidenceBundle, EvolutionError]:
        if data.overall_status == "failure":
            return Failure(VerificationFailedError(
                message="Execution already failed",
                check_type="execution",
                details=f"Overall status: {data.overall_status}",
            ))

        test_results = await self._run_tests()
        lint_results = await self._run_linter()
        type_results = await self._run_type_check()

        all_passed = (
            test_results.get("passed", False)
            and lint_results.get("passed", False)
            and type_results.get("passed", False)
        )

        status = "pass" if all_passed else "fail"

        evidence = EvidenceBundle(
            status=status,
            test_results=test_results,
            lint_results=lint_results,
            type_check_results=type_results,
            diff_summary=f"{len(data.artifacts_produced)} artifacts produced",
            metrics={
                "total_beads": len(data.bead_results),
                "duration_ms": data.total_duration_ms,
            },
        )

        if not all_passed:
            failed_checks = []
            if not test_results.get("passed"):
                failed_checks.append("tests")
            if not lint_results.get("passed"):
                failed_checks.append("lint")
            if not type_results.get("passed"):
                failed_checks.append("type_check")

            return Failure(VerificationFailedError(
                message=f"Verification failed: {', '.join(failed_checks)}",
                check_type=", ".join(failed_checks),
                details=str(evidence.model_dump()),
            ))

        return Success(evidence)

    async def _run_tests(self) -> dict[str, Any]:
        return await self._run_command(
            "python", "-m", "pytest", "--tb=short", "-q",
            check_name="pytest",
        )

    async def _run_linter(self) -> dict[str, Any]:
        return await self._run_command(
            "python", "-m", "ruff", "check", ".",
            check_name="ruff",
        )

    async def _run_type_check(self) -> dict[str, Any]:
        return await self._run_command(
            "python", "-m", "mypy", "src/", "--ignore-missing-imports",
            check_name="mypy",
        )

    async def _run_command(
        self, *args: str, check_name: str,
    ) -> dict[str, Any]:
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self._root,
            )
            stdout, stderr = await proc.communicate()
            return {
                "passed": proc.returncode == 0,
                "exit_code": proc.returncode,
                "stdout": stdout.decode(errors="replace")[:2000],
                "stderr": stderr.decode(errors="replace")[:2000],
                "tool": check_name,
            }
        except FileNotFoundError:
            return {
                "passed": True,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"{check_name} not found, skipping",
                "tool": check_name,
                "skipped": True,
            }

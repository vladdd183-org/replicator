from __future__ import annotations

import os
import time

import anyio
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.CoreSection.SpecModule.Data.Schemas.Models import (
    DetailedBead,
    DetailedBeadGraph,
    BeadExecutionResult,
    MissionExecutionResult,
)
from src.Containers.AgentSection.OrchestratorModule.Errors import (
    OrchestratorError,
    BeadExecutionError,
)
from src.Containers.AgentSection.OrchestratorModule.Actions.FinalizeMissionAction import (
    FinalizeMissionAction,
)

BD_CMD = "/home/vladdd183/.local/bin/bd-wrapper"


class ExecuteDetailedBeadAction(Action[DetailedBead, BeadExecutionResult, OrchestratorError]):
    """Воркер-исполнитель: НЕ думает, просто записывает файлы и выполняет команды.

    Интегрирован с Beads: claim перед исполнением, close после.
    """

    def __init__(self, project_root: str = ".", bd_bead_id: str = "") -> None:
        self._root = project_root
        self._bd_id = bd_bead_id

    async def run(self, data: DetailedBead) -> Result[BeadExecutionResult, OrchestratorError]:
        start = time.monotonic()
        files_written: list[str] = []
        commands_executed: list[str] = []

        try:
            if self._bd_id:
                await self._bd_claim(self._bd_id)

            for op in data.file_operations:
                full_path = os.path.join(self._root, op.file_path)

                if op.action in ("create", "modify"):
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    async_path = anyio.Path(full_path)
                    await async_path.write_text(op.content, encoding="utf-8")
                    files_written.append(op.file_path)

                elif op.action == "delete":
                    async_path = anyio.Path(full_path)
                    if await async_path.exists():
                        await async_path.unlink()
                        files_written.append(f"(deleted) {op.file_path}")

            for cmd in data.shell_commands:
                try:
                    result = await anyio.run_process(
                        ["bash", "-c", cmd],
                        cwd=self._root,
                        check=False,
                    )
                    commands_executed.append(f"{cmd} -> exit {result.returncode}")
                except Exception as e:
                    commands_executed.append(f"{cmd} -> error: {e}")

            commit_hash = ""
            if files_written:
                msg = f"bead: {data.title}"
                if self._bd_id:
                    msg = f"bead: {data.title} ({self._bd_id})"
                commit_hash = await self._git_commit(msg, files_written)

            if self._bd_id:
                await self._bd_close(self._bd_id)

            duration = int((time.monotonic() - start) * 1000)

            return Success(BeadExecutionResult(
                bead_id=data.id,
                bead_title=data.title,
                status="success",
                files_written=files_written,
                commands_executed=commands_executed,
                duration_ms=duration,
                commit_hash=commit_hash,
                bd_bead_id=self._bd_id,
            ))

        except Exception as e:
            return Failure(BeadExecutionError(
                message=f"Bead execution failed: {e}",
            ))

    async def _bd_claim(self, bead_id: str) -> None:
        await anyio.run_process(
            [BD_CMD, "update", bead_id, "--claim", "--json"],
            cwd=self._root, check=False,
        )

    async def _bd_close(self, bead_id: str) -> None:
        await anyio.run_process(
            [BD_CMD, "close", bead_id, "--reason", "Completed", "--json"],
            cwd=self._root, check=False,
        )

    async def _git_commit(self, message: str, files: list[str]) -> str:
        try:
            real_files = [f for f in files if not f.startswith("(deleted)")]
            if real_files:
                await anyio.run_process(
                    ["git", "add"] + real_files,
                    cwd=self._root, check=False,
                )

            result = await anyio.run_process(
                ["git", "commit", "-m", message, "--allow-empty"],
                cwd=self._root, check=False,
            )

            if result.returncode == 0:
                hash_result = await anyio.run_process(
                    ["git", "rev-parse", "HEAD"],
                    cwd=self._root,
                )
                return hash_result.stdout.decode().strip()[:12]
        except Exception:
            pass
        return ""


class ExecuteDetailedGraphAction(Action[DetailedBeadGraph, MissionExecutionResult, OrchestratorError]):
    """Исполняет DetailedBeadGraph с интеграцией Beads и Git.

    1. Создаёт git branch
    2. Для каждого bead: bd claim -> write files -> git commit -> bd close
    3. Beads параллельно внутри групп (anyio TaskGroup)
    4. После успеха: push, PR, auto-merge (FinalizeMission)
    """

    def __init__(
        self,
        project_root: str = ".",
        bd_bead_ids: dict[str, str] | None = None,
    ) -> None:
        self._root = project_root
        self._bd_ids = bd_bead_ids or {}

    async def run(self, data: DetailedBeadGraph) -> Result[MissionExecutionResult, OrchestratorError]:
        start = time.monotonic()
        all_results: list[BeadExecutionResult] = []

        try:
            if data.git_branch:
                await self._create_branch(data.git_branch)

            bead_map = {b.id: b for b in data.beads}

            for group in data.parallel_groups:
                group_beads = [bead_map[bid] for bid in group if bid in bead_map]
                group_results: list[BeadExecutionResult] = []

                async with anyio.create_task_group() as tg:
                    for bead in group_beads:
                        bd_id = self._bd_ids.get(bead.id, "")

                        async def exec_one(b: DetailedBead = bead, bid: str = bd_id) -> None:
                            executor = ExecuteDetailedBeadAction(
                                project_root=self._root,
                                bd_bead_id=bid,
                            )
                            result = await executor.run(b)
                            if isinstance(result, Success):
                                group_results.append(result.unwrap())
                            else:
                                group_results.append(BeadExecutionResult(
                                    bead_id=b.id,
                                    bead_title=b.title,
                                    status="failure",
                                    error_message=str(result.failure()),
                                    bd_bead_id=bid,
                                ))
                        tg.start_soon(exec_one)

                all_results.extend(group_results)

                if any(r.status == "failure" for r in group_results):
                    break

            duration = int((time.monotonic() - start) * 1000)
            overall = "success" if all(r.status == "success" for r in all_results) else "failure"
            total_files = sum(len(r.files_written) for r in all_results)
            total_commits = sum(1 for r in all_results if r.commit_hash)

            mission = MissionExecutionResult(
                mission_title=data.mission_title,
                git_branch=data.git_branch,
                bead_results=all_results,
                overall_status=overall,
                total_duration_ms=duration,
                total_files_changed=total_files,
                total_commits=total_commits,
            )

            if overall == "success" and data.git_branch:
                fin = FinalizeMissionAction(project_root=self._root)
                fin_res = await fin.run(mission)
                if isinstance(fin_res, Success):
                    mission = mission.model_copy(update={"finalize": fin_res.unwrap()})
                else:
                    mission = mission.model_copy(
                        update={"finalize": {"error": str(fin_res.failure())}},
                    )

            return Success(mission)

        except Exception as e:
            return Failure(BeadExecutionError(
                message=f"Graph execution failed: {e}",
            ))

    async def _create_branch(self, branch: str) -> None:
        await anyio.run_process(
            ["git", "checkout", "-B", branch],
            cwd=self._root, check=False,
        )

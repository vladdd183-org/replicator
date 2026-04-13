from __future__ import annotations

import json
import time
from typing import Any

import anyio
from returns.result import Failure, Result, Success

from src.Containers.AgentSection.OrchestratorModule.Errors import (
    BeadExecutionError,
    OrchestratorError,
)
from src.Containers.CoreSection.SpecModule.Data.Schemas.Models import (
    Bead,
    BeadGraph,
    BeadResult,
    ExecutionResult,
)
from src.Ship.Parents.Action import Action


class ExecuteBeadGraphAction(Action[BeadGraph, ExecutionResult, OrchestratorError]):
    """Исполняет BeadGraph: параллельные группы через быструю модель.
    
    Использует gpt-oss-120b на Cerebras (569+ tok/s) для массового
    параллельного исполнения бидов.
    """

    def __init__(
        self,
        llm_client: Any = None,
        compute_port: Any = None,
        model: str = "openai/gpt-oss-120b",
    ) -> None:
        self._llm = llm_client
        self._compute = compute_port
        self._model = model

    async def run(self, data: BeadGraph) -> Result[ExecutionResult, OrchestratorError]:
        start = time.monotonic()
        results: list[BeadResult] = []

        try:
            execution_order = self._topological_sort(data)

            for group in execution_order:
                group_results = await self._execute_group(group, results)
                results.extend(group_results)

                if any(r.status == "failure" for r in group_results):
                    break

            duration = int((time.monotonic() - start) * 1000)
            overall = "success" if all(r.status == "success" for r in results) else "failure"

            return Success(ExecutionResult(
                bead_results=results,
                overall_status=overall,
                total_duration_ms=duration,
                artifacts_produced=[a for r in results for a in r.artifacts],
            ))

        except Exception as e:
            return Failure(BeadExecutionError(
                message=f"Graph execution failed: {e}",
            ))

    def _topological_sort(self, graph: BeadGraph) -> list[list[Bead]]:
        """Группировка бидов: параллельно внутри группы, последовательно между."""
        if graph.parallel_groups:
            bead_map = {b.id: b for b in graph.beads}
            return [
                [bead_map[bid] for bid in group if bid in bead_map]
                for group in graph.parallel_groups
            ]
        return [[b] for b in graph.beads]

    async def _execute_group(
        self, beads: list[Bead], prior_results: list[BeadResult],
    ) -> list[BeadResult]:
        """Параллельное исполнение группы бидов через anyio TaskGroup."""
        results: list[BeadResult] = []

        async with anyio.create_task_group() as tg:
            for bead in beads:
                async def execute_one(b: Bead = bead) -> None:
                    result = await self._execute_bead(b, prior_results)
                    results.append(result)
                tg.start_soon(execute_one)

        return results

    async def _execute_bead(
        self, bead: Bead, prior_results: list[BeadResult],
    ) -> BeadResult:
        """Исполнение одного бида через LLM."""
        start = time.monotonic()

        try:
            if self._llm is None:
                return BeadResult(
                    bead_id=bead.id,
                    status="success",
                    evidence={"note": "No LLM available, bead marked as success (dry run)"},
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            context = self._build_context(bead, prior_results)

            response = await self._llm.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an AI developer executing a specific task (bead). "
                            "Return the result as JSON with keys: "
                            "'artifacts' (list of produced items), "
                            "'evidence' (dict of proof), 'notes' (str)."
                        ),
                    },
                    {"role": "user", "content": context},
                ],
                temperature=0.2,
            )

            raw = response.choices[0].message.content.strip()
            duration = int((time.monotonic() - start) * 1000)

            return BeadResult(
                bead_id=bead.id,
                status="success",
                artifacts=[],
                evidence={"llm_response": raw[:2000]},
                duration_ms=duration,
                agent_id="orchestrator-executor",
            )

        except Exception as e:
            return BeadResult(
                bead_id=bead.id,
                status="failure",
                error_message=str(e),
                duration_ms=int((time.monotonic() - start) * 1000),
            )

    def _build_context(self, bead: Bead, prior_results: list[BeadResult]) -> str:
        parts = [
            f"## Bead: {bead.title}",
            f"Description: {bead.description}",
            f"Type: {bead.bead_type.value}",
            f"Acceptance Criteria: {json.dumps(bead.acceptance_criteria)}",
            f"Tools Required: {json.dumps(bead.tools_required)}",
        ]
        if prior_results:
            parts.append(f"\n## Prior Results ({len(prior_results)} completed beads)")
            for r in prior_results[-3:]:
                parts.append(f"- Bead {r.bead_id}: {r.status}")
        return "\n".join(parts)

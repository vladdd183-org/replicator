from __future__ import annotations

import json
import time
from typing import Any

from returns.result import Failure, Result, Success

from src.Containers.AgentSection.OrchestratorModule.Errors import (
    BeadExecutionError,
    OrchestratorError,
)
from src.Containers.CoreSection.SpecModule.Data.Schemas.Models import (
    Bead,
    BeadResult,
)
from src.Ship.Parents.Action import Action


class ExecuteBeadAction(Action[Bead, BeadResult, OrchestratorError]):
    """Исполняет один бид: делегирует в LLM или ComputePort."""

    def __init__(self, llm_client: Any = None, compute_port: Any = None) -> None:
        self._llm = llm_client
        self._compute = compute_port

    async def run(self, data: Bead) -> Result[BeadResult, OrchestratorError]:
        start = time.monotonic()

        try:
            if self._compute is not None and data.bead_type.value in ("code", "test"):
                return await self._execute_via_compute(data, start)

            if self._llm is not None:
                return await self._execute_via_llm(data, start)

            return Success(BeadResult(
                bead_id=data.id,
                status="success",
                evidence={"note": "Dry run -- no LLM or compute available"},
                duration_ms=int((time.monotonic() - start) * 1000),
                agent_id="orchestrator-dry-run",
            ))

        except Exception as e:
            return Failure(BeadExecutionError(
                message=f"Bead execution failed: {e}",
                bead_id=data.id,
            ))

    async def _execute_via_llm(
        self, bead: Bead, start: float,
    ) -> Result[BeadResult, OrchestratorError]:
        """Исполнение бида через LLM."""
        prompt = self._build_prompt(bead)

        response = await self._llm.chat.completions.create(
            model="anthropic/claude-sonnet-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI developer executing an atomic task. "
                        "Return JSON: {\"artifacts\": [], \"evidence\": {}, \"notes\": \"\"}"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        raw = response.choices[0].message.content.strip()
        duration = int((time.monotonic() - start) * 1000)

        return Success(BeadResult(
            bead_id=bead.id,
            status="success",
            evidence={"llm_response": raw[:2000]},
            duration_ms=duration,
            agent_id="orchestrator-llm",
        ))

    async def _execute_via_compute(
        self, bead: Bead, start: float,
    ) -> Result[BeadResult, OrchestratorError]:
        """Исполнение через ComputePort (Nix sandbox, Docker и т.д.)."""
        compute_result = await self._compute.execute(
            command=f"echo 'Executing bead: {bead.title}'",
            sandbox=True,
        )

        duration = int((time.monotonic() - start) * 1000)

        return Success(BeadResult(
            bead_id=bead.id,
            status="success" if compute_result.exit_code == 0 else "failure",
            evidence={
                "output": compute_result.output.decode(errors="replace")[:2000],
                "exit_code": compute_result.exit_code,
            },
            duration_ms=duration,
            agent_id="orchestrator-compute",
            error_message="" if compute_result.exit_code == 0 else "Non-zero exit code",
        ))

    def _build_prompt(self, bead: Bead) -> str:
        return "\n".join([
            f"## Bead: {bead.title}",
            f"Description: {bead.description}",
            f"Type: {bead.bead_type.value}",
            f"Acceptance Criteria: {json.dumps(bead.acceptance_criteria)}",
            f"Tools Required: {json.dumps(bead.tools_required)}",
        ])

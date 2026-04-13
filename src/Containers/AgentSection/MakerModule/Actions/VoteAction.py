from __future__ import annotations

import json
import time
from typing import Any

import anyio
from pydantic import BaseModel, Field
from returns.result import Failure, Result, Success

from src.Containers.AgentSection.MakerModule.Errors import MakerError, NoConsensusError
from src.Containers.CoreSection.SpecModule.Data.Schemas.Models import (
    Bead,
    BeadResult,
)
from src.Ship.Parents.Action import Action


class VoteRequest(BaseModel):
    """Запрос на K-голосование по биду."""

    model_config = {"frozen": True}

    bead: Bead
    k: int = 1
    prompt: str = ""


class VoteAction(Action[VoteRequest, BeadResult, MakerError]):
    """K-Voting: запускает K параллельных агентов и выбирает лучший результат."""

    def __init__(self, llm_client: Any = None) -> None:
        self._llm = llm_client

    async def run(self, data: VoteRequest) -> Result[BeadResult, MakerError]:
        start = time.monotonic()

        try:
            if self._llm is None:
                return self._dry_run(data, start)

            if data.k <= 1:
                result = await self._execute_single(data)
                return Success(result)

            return await self._execute_k_voting(data, start)

        except Exception as e:
            return Failure(NoConsensusError(
                message=f"Vote execution failed: {e}",
                bead_id=data.bead.id,
                k=data.k,
            ))

    def _dry_run(
        self, data: VoteRequest, start: float,
    ) -> Result[BeadResult, MakerError]:
        """Dry-run без LLM."""
        return Success(BeadResult(
            bead_id=data.bead.id,
            status="success",
            evidence={"note": "Dry run -- no LLM available"},
            duration_ms=int((time.monotonic() - start) * 1000),
            agent_id="maker-dry-run",
        ))

    async def _execute_single(self, data: VoteRequest) -> BeadResult:
        """Исполнение одним агентом (K=1)."""
        start = time.monotonic()

        context = self._build_prompt(data)
        response = await self._llm.chat.completions.create(
            model="anthropic/claude-sonnet-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a MAKER agent executing an atomic task (bead). "
                        "Return JSON: {\"artifacts\": [], \"evidence\": {}, \"notes\": \"\"}"
                    ),
                },
                {"role": "user", "content": context},
            ],
            temperature=0.2,
        )

        raw = response.choices[0].message.content.strip()
        duration = int((time.monotonic() - start) * 1000)

        return BeadResult(
            bead_id=data.bead.id,
            status="success",
            evidence={"llm_response": raw[:2000]},
            duration_ms=duration,
            agent_id="maker-single",
        )

    async def _execute_k_voting(
        self, data: VoteRequest, start: float,
    ) -> Result[BeadResult, MakerError]:
        """Параллельное K-голосование через anyio TaskGroup."""
        candidates: list[BeadResult] = []

        async with anyio.create_task_group() as tg:
            for i in range(data.k):
                async def run_agent(agent_idx: int = i) -> None:
                    result = await self._execute_single(
                        VoteRequest(
                            bead=data.bead,
                            k=1,
                            prompt=data.prompt,
                        ),
                    )
                    result_with_agent = BeadResult(
                        bead_id=result.bead_id,
                        status=result.status,
                        artifacts=result.artifacts,
                        evidence=result.evidence,
                        duration_ms=result.duration_ms,
                        agent_id=f"maker-vote-{agent_idx}",
                        error_message=result.error_message,
                    )
                    candidates.append(result_with_agent)
                tg.start_soon(run_agent)

        if not candidates:
            return Failure(NoConsensusError(
                message="No candidates produced during K-voting",
                bead_id=data.bead.id,
                k=data.k,
                attempts=data.k,
            ))

        best = self._pick_best(candidates)
        return Success(best)

    def _pick_best(self, candidates: list[BeadResult]) -> BeadResult:
        """Выбирает лучший результат из кандидатов.
        
        MVP: первый успешный; при отсутствии -- первый любой.
        """
        successful = [c for c in candidates if c.status == "success"]
        return successful[0] if successful else candidates[0]

    def _build_prompt(self, data: VoteRequest) -> str:
        bead = data.bead
        parts = [
            f"## Bead: {bead.title}",
            f"Description: {bead.description}",
            f"Type: {bead.bead_type.value}",
            f"Acceptance Criteria: {json.dumps(bead.acceptance_criteria)}",
            f"Tools Required: {json.dumps(bead.tools_required)}",
        ]
        if data.prompt:
            parts.append(f"\n## Additional context:\n{data.prompt}")
        return "\n".join(parts)

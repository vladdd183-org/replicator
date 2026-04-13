from __future__ import annotations

import json
from typing import Any

from returns.result import Failure, Result, Success

from src.Containers.AgentSection.CompassModule.Errors import (
    CompassError,
    StrategyFormationError,
)
from src.Containers.CoreSection.SpecModule.Data.Schemas.Models import (
    MissionSpec,
    StrategyPlan,
    StrategyPhase,
)
from src.Ship.Parents.Action import Action

_SYSTEM_PROMPT = """You are a strategic AI planner (COMPASS Meta-Thinker).
Given a MissionSpec, produce a StrategyPlan as JSON:
{
    "approach": "high-level approach description",
    "phases": [
        {"name": "phase name", "description": "what to do", "dependencies": [], "parallel": false}
    ],
    "risk_mitigations": ["mitigation 1"],
    "rollback_plan": "how to rollback",
    "estimated_beads": 5,
    "confidence": 0.8
}
Be specific and actionable. For code changes, describe exact files and modifications."""


class StrategizeAction(Action[MissionSpec, StrategyPlan, CompassError]):
    """Meta-Thinker: формирует стратегию исполнения из MissionSpec."""

    def __init__(self, llm_client: Any = None) -> None:
        self._llm = llm_client

    async def run(self, data: MissionSpec) -> Result[StrategyPlan, CompassError]:
        if self._llm is not None:
            try:
                return await self._strategize_with_llm(data)
            except Exception:
                pass
        return self._strategize_heuristic(data)

    async def _strategize_with_llm(
        self, spec: MissionSpec,
    ) -> Result[StrategyPlan, CompassError]:
        """Формирование стратегии через LLM."""
        spec_text = (
            f"Title: {spec.title}\n"
            f"Description: {spec.description}\n"
            f"Intent Type: {spec.intent_type.value}\n"
            f"Target: {spec.target}\n"
            f"Acceptance Criteria: {json.dumps(spec.acceptance_criteria)}\n"
            f"Constraints: {json.dumps(spec.constraints)}\n"
            f"Priority: {spec.priority.value}"
        )

        response = await self._llm.chat.completions.create(
            model="anthropic/claude-sonnet-4",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": spec_text},
            ],
            temperature=0.3,
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)

        phases = [
            StrategyPhase(
                name=p["name"],
                description=p["description"],
                dependencies=p.get("dependencies", []),
                parallel=p.get("parallel", False),
            )
            for p in parsed.get("phases", [])
        ]

        plan = StrategyPlan(
            approach=parsed["approach"],
            phases=phases,
            risk_mitigations=parsed.get("risk_mitigations", []),
            rollback_plan=parsed.get("rollback_plan", ""),
            estimated_beads=parsed.get("estimated_beads", len(phases)),
            confidence=parsed.get("confidence", 0.7),
        )
        return Success(plan)

    def _strategize_heuristic(
        self, spec: MissionSpec,
    ) -> Result[StrategyPlan, CompassError]:
        """Эвристическая стратегия без LLM."""
        phase = StrategyPhase(
            name="execute",
            description=f"Execute: {spec.description[:200]}",
        )
        plan = StrategyPlan(
            approach=f"Direct execution of: {spec.title}",
            phases=[phase],
            estimated_beads=1,
            confidence=0.5,
        )
        return Success(plan)

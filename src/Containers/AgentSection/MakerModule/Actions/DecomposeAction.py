from __future__ import annotations

import json
import uuid
from typing import Any

from returns.result import Failure, Result, Success

from src.Containers.AgentSection.MakerModule.Errors import (
    DecompositionError,
    MakerError,
)
from src.Containers.CoreSection.SpecModule.Data.Schemas.Models import (
    Bead,
    BeadGraph,
    StrategyPlan,
)
from src.Ship.Core.Types import BeadType, Complexity
from src.Ship.Parents.Action import Action

_SYSTEM_PROMPT = """You are MAKER Decomposer. Given a StrategyPlan, decompose each phase into atomic beads.
Return JSON:
{
    "beads": [
        {
            "title": "bead title",
            "description": "what exactly to do",
            "bead_type": "code|test|config|doc|review",
            "acceptance_criteria": ["criterion 1"],
            "dependencies": ["bead-id-of-dependency"],
            "tools_required": ["tool1"],
            "estimated_complexity": "trivial|simple|moderate|complex"
        }
    ],
    "parallel_groups": [["bead-0"], ["bead-1", "bead-2"], ["bead-3"]]
}
Each bead should be atomic -- completable in a single agent turn.
Use bead indices (bead-0, bead-1, ...) for dependencies and parallel_groups."""


class DecomposeAction(Action[StrategyPlan, BeadGraph, MakerError]):
    """MAKER Decomposer: декомпозирует StrategyPlan в BeadGraph.
    
    Использует быструю модель-воркер (gpt-oss-120b на Cerebras).
    """

    def __init__(self, llm_client: Any = None, model: str = "openai/gpt-oss-120b") -> None:
        self._llm = llm_client
        self._model = model

    async def run(self, data: StrategyPlan) -> Result[BeadGraph, MakerError]:
        if self._llm is not None:
            try:
                return await self._decompose_with_llm(data)
            except Exception:
                pass
        return self._decompose_heuristic(data)

    async def _decompose_with_llm(
        self, plan: StrategyPlan,
    ) -> Result[BeadGraph, MakerError]:
        """Декомпозиция через быструю модель (MAKER)."""
        plan_text = (
            f"Approach: {plan.approach}\n"
            f"Confidence: {plan.confidence}\n"
            f"Phases:\n"
        )
        for i, phase in enumerate(plan.phases):
            plan_text += (
                f"  {i}. {phase.name}: {phase.description}"
                f" (deps={phase.dependencies}, parallel={phase.parallel})\n"
            )
        plan_text += f"Risk mitigations: {json.dumps(plan.risk_mitigations)}\n"
        plan_text += f"Rollback plan: {plan.rollback_plan}\n"

        response = await self._llm.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": plan_text},
            ],
            temperature=0.2,
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)
        return self._build_graph_from_parsed(parsed)

    def _decompose_heuristic(
        self, plan: StrategyPlan,
    ) -> Result[BeadGraph, MakerError]:
        """Один CODE bead на каждую фазу."""
        beads: list[Bead] = []
        edges: list[tuple[str, str]] = []
        prev_id: str | None = None

        for phase in plan.phases:
            bead_id = str(uuid.uuid4())
            bead = Bead(
                id=bead_id,
                title=phase.name,
                description=phase.description,
                bead_type=BeadType.CODE,
                acceptance_criteria=[f"Phase '{phase.name}' completed"],
            )
            beads.append(bead)

            if prev_id is not None and not phase.parallel:
                edges.append((prev_id, bead_id))
            prev_id = bead_id

        parallel_groups = [[b.id] for b in beads]

        graph = BeadGraph(
            beads=beads,
            edges=edges,
            critical_path=[b.id for b in beads],
            parallel_groups=parallel_groups,
        )
        return Success(graph)

    def _build_graph_from_parsed(
        self, parsed: dict[str, Any],
    ) -> Result[BeadGraph, MakerError]:
        """Собирает BeadGraph из JSON-ответа LLM."""
        raw_beads = parsed.get("beads", [])
        id_map: dict[str, str] = {}
        beads: list[Bead] = []

        complexity_map = {v.value: v for v in Complexity}
        bead_type_map = {v.value: v for v in BeadType}

        for i, rb in enumerate(raw_beads):
            bead_id = str(uuid.uuid4())
            idx_key = f"bead-{i}"
            id_map[idx_key] = bead_id

            bead = Bead(
                id=bead_id,
                title=rb.get("title", f"Bead {i}"),
                description=rb.get("description", ""),
                bead_type=bead_type_map.get(
                    rb.get("bead_type", "code"), BeadType.CODE,
                ),
                acceptance_criteria=rb.get("acceptance_criteria", []),
                tools_required=rb.get("tools_required", []),
                estimated_complexity=complexity_map.get(
                    rb.get("estimated_complexity", "simple"), Complexity.SIMPLE,
                ),
            )
            beads.append(bead)

        edges: list[tuple[str, str]] = []
        for i, rb in enumerate(raw_beads):
            bead_id = id_map[f"bead-{i}"]
            for dep_key in rb.get("dependencies", []):
                if dep_key in id_map:
                    edges.append((id_map[dep_key], bead_id))

        raw_groups = parsed.get("parallel_groups", [])
        parallel_groups: list[list[str]] = []
        for group in raw_groups:
            resolved = [id_map[k] for k in group if k in id_map]
            if resolved:
                parallel_groups.append(resolved)

        if not parallel_groups:
            parallel_groups = [[b.id] for b in beads]

        critical_path = [b.id for b in beads]

        graph = BeadGraph(
            beads=beads,
            edges=edges,
            critical_path=critical_path,
            parallel_groups=parallel_groups,
        )
        return Success(graph)

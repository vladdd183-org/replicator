from __future__ import annotations

import json
from typing import Any

from returns.result import Failure, Result, Success

from src.Containers.CoreSection.SpecModule.Data.Schemas.Models import MissionSpec
from src.Containers.CoreSection.SpecModule.Errors import SpecCompilationError
from src.Ship.Core.Types import IntentType, Priority
from src.Ship.Parents.Action import Action

_SYSTEM_PROMPT = """You are a spec compiler. Given a user intent, produce a JSON MissionSpec:
{
    "title": "short title",
    "description": "full description",
    "intent_type": "self_evolve|generate|legacy",
    "target": "self or repo URL",
    "acceptance_criteria": ["..."],
    "constraints": ["..."],
    "risks": ["..."],
    "priority": "critical|high|medium|low"
}
Respond ONLY with valid JSON."""

_GENERATE_KEYWORDS = ("создать", "generate", "new project", "новый проект")
_LEGACY_KEYWORDS = ("legacy", "существующ", "existing", "fix", "исправ")


class CompileSpecAction(Action[str, MissionSpec, SpecCompilationError]):
    """Компилирует текстовый intent в структурированную MissionSpec."""

    def __init__(self, llm_client: Any = None) -> None:
        self._llm = llm_client

    async def run(self, data: str) -> Result[MissionSpec, SpecCompilationError]:
        if self._llm is not None:
            try:
                return await self._compile_with_llm(data)
            except Exception:
                pass
        return self._compile_heuristic(data)

    async def _compile_with_llm(
        self, intent: str,
    ) -> Result[MissionSpec, SpecCompilationError]:
        """Компиляция intent через LLM."""
        response = await self._llm.chat.completions.create(
            model="anthropic/claude-sonnet-4",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": intent},
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
        spec = MissionSpec(
            title=parsed.get("title", intent[:50]),
            description=parsed.get("description", intent),
            intent_type=IntentType(parsed.get("intent_type", "self_evolve")),
            target=parsed.get("target", "self"),
            acceptance_criteria=parsed.get("acceptance_criteria", []),
            constraints=parsed.get("constraints", []),
            risks=parsed.get("risks", []),
            priority=Priority(parsed.get("priority", "medium")),
        )
        return Success(spec)

    def _compile_heuristic(
        self, intent: str,
    ) -> Result[MissionSpec, SpecCompilationError]:
        """Простая эвристическая компиляция без LLM."""
        intent_lower = intent.lower()

        if any(kw in intent_lower for kw in _GENERATE_KEYWORDS):
            intent_type = IntentType.GENERATE
        elif any(kw in intent_lower for kw in _LEGACY_KEYWORDS):
            intent_type = IntentType.LEGACY
        else:
            intent_type = IntentType.SELF_EVOLVE

        spec = MissionSpec(
            title=intent[:80],
            description=intent,
            intent_type=intent_type,
            acceptance_criteria=[f"Intent fulfilled: {intent[:100]}"],
        )
        return Success(spec)

from __future__ import annotations

import json
import os
import time
from typing import Any

import anyio
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.CoreSection.SpecModule.Data.Schemas.Models import (
    MissionSpec,
    DetailedBead,
    DetailedBeadGraph,
    FileOperation,
)
from src.Containers.AgentSection.CompassModule.Errors import CompassError, StrategyFormationError
from src.Ship.Core.Types import BeadType, Complexity

BD_CMD = "/home/vladdd183/.local/bin/bd-wrapper"


_OPUS_SYSTEM_PROMPT = """Ты -- COMPASS Meta-Thinker, мозг системы Replicator.

Твоя задача: получить intent и ПОЛНОСТЬЮ спланировать его реализацию.
Ты продумываешь ВСЁ. Воркеры, которые будут исполнять твой план, НЕ ДУМАЮТ.
Они просто записывают файлы и выполняют команды которые ты указал.

ПРАВИЛА:
1. Анализируй текущую структуру проекта (она дана ниже)
2. Формируй КОНКРЕТНЫЕ файловые операции с ПОЛНЫМ кодом файлов
3. Каждый bead должен быть атомарным -- одна логическая единица работы
4. Для каждого bead указывай file_operations с action (create/modify/delete) и полным content
5. Указывай shell_commands если нужно (тесты, линтеры)
6. Группируй beads в parallel_groups -- независимые beads в одну группу
7. Весь код должен следовать Porto-архитектуре: абсолютные импорты от src/, Result[T,E], frozen Pydantic

ФОРМАТ ОТВЕТА (строго JSON):
{
    "mission_title": "краткое название",
    "git_branch": "feature/название-фичи",
    "beads": [
        {
            "title": "название bead",
            "description": "что делает",
            "bead_type": "code|test|config|doc",
            "file_operations": [
                {
                    "action": "create|modify|delete",
                    "file_path": "src/путь/к/файлу.py",
                    "content": "полный контент файла",
                    "description": "зачем"
                }
            ],
            "shell_commands": ["uv run pytest tests/...", "uv run ruff check src/..."],
            "acceptance_criteria": ["что должно быть true"],
            "estimated_complexity": "trivial|simple|moderate|complex"
        }
    ],
    "parallel_groups": [["bead-0"], ["bead-1", "bead-2"], ["bead-3"]]
}

Используй bead-0, bead-1, ... как ID в parallel_groups.
Пиши КОД, а не заглушки. Пиши РЕАЛЬНЫЙ рабочий код.
ВАЖНО: каждый файл не более 150 строк. Если файл большой -- разбей на несколько beads.
Отвечай ТОЛЬКО валидным JSON, без markdown."""


class PlanMissionAction(Action[MissionSpec, DetailedBeadGraph, CompassError]):
    """COMPASS Meta-Thinker: Opus продумывает ВСЁ, воркеры просто исполняют.

    Использует Opus 4.6 для глубокого анализа и генерации
    детальных bead-инструкций с готовым кодом.
    """

    def __init__(
        self,
        llm_client: Any = None,
        model: str = "anthropic/claude-opus-4",
        project_root: str = ".",
    ) -> None:
        self._llm = llm_client
        self._model = model
        self._root = project_root

    async def run(self, data: MissionSpec) -> Result[DetailedBeadGraph, CompassError]:
        if self._llm is None:
            return Failure(StrategyFormationError(
                message="LLM client required for PlanMissionAction",
            ))

        try:
            return await self._plan_with_opus(data)
        except Exception as e:
            return Failure(StrategyFormationError(
                message=f"Planning failed: {e}",
            ))

    async def _plan_with_opus(
        self, spec: MissionSpec,
    ) -> Result[DetailedBeadGraph, CompassError]:
        project_structure = self._scan_project_structure()

        user_prompt = self._build_prompt(spec, project_structure)

        response = await self._llm.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _OPUS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=64000,
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:])
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        parsed = self._parse_json_robust(raw)
        return self._build_graph(parsed)

    @staticmethod
    def _parse_json_robust(raw: str) -> dict[str, Any]:
        """Парсинг JSON с recovery для обрезанных ответов."""
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        for trim in ['"}]}', '"}],"parallel_groups":[]}', '"]},{"title":', '"}]}']:
            try:
                return json.loads(raw + trim)
            except json.JSONDecodeError:
                continue

        last_brace = raw.rfind("}")
        if last_brace > 0:
            candidate = raw[:last_brace + 1]
            bracket_count = candidate.count("[") - candidate.count("]")
            brace_count = candidate.count("{") - candidate.count("}")
            candidate += "]" * bracket_count + "}" * brace_count
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        raise json.JSONDecodeError("Could not recover truncated JSON", raw, 0)

    def _scan_project_structure(self) -> str:
        """Scan project directory for context."""
        lines = []
        scan_root = self._root
        skip_dirs = {"__pycache__", ".git", ".beads", "node_modules", ".venv", ".nix", ".obsidian"}

        for root, dirs, files in os.walk(scan_root):
            dirs[:] = sorted(d for d in dirs if d not in skip_dirs and not d.startswith("."))
            level = root.replace(scan_root, "").count(os.sep)
            indent = "  " * level
            dirname = os.path.basename(root)
            lines.append(f"{indent}{dirname}/")

            sub_indent = "  " * (level + 1)
            code_exts = {".py", ".ts", ".js", ".go", ".rs", ".nix", ".md", ".toml", ".yaml", ".yml"}
            code_files = [f for f in sorted(files) if any(f.endswith(e) for e in code_exts)]
            for f in code_files[:15]:
                lines.append(f"{sub_indent}{f}")

            if len(lines) > 300:
                lines.append("... (truncated)")
                break

        return "\n".join(lines)

    def _build_prompt(self, spec: MissionSpec, structure: str) -> str:
        return f"""## МИССИЯ
Название: {spec.title}
Описание: {spec.description}
Тип: {spec.intent_type.value}
Цель: {spec.target}
Приоритет: {spec.priority.value}

## Acceptance Criteria
{json.dumps(spec.acceptance_criteria, ensure_ascii=False, indent=2)}

## Constraints
{json.dumps(spec.constraints, ensure_ascii=False, indent=2)}

## ТЕКУЩАЯ СТРУКТУРА ПРОЕКТА
```
{structure}
```

## ЗАДАЧА
Создай детальный план реализации. Для каждого bead укажи ТОЧНЫЕ файловые операции с полным кодом.
Воркеры не думают -- они просто записывают файлы которые ты укажешь."""

    def _build_graph(self, parsed: dict[str, Any]) -> Result[DetailedBeadGraph, CompassError]:
        import uuid as _uuid

        raw_beads = parsed.get("beads", [])
        beads: list[DetailedBead] = []
        id_map: dict[str, str] = {}

        for i, rb in enumerate(raw_beads):
            bead_id = str(_uuid.uuid4())
            id_map[f"bead-{i}"] = bead_id

            file_ops = [
                FileOperation(
                    action=op.get("action", "create"),
                    file_path=op.get("file_path", ""),
                    content=op.get("content", ""),
                    description=op.get("description", ""),
                )
                for op in rb.get("file_operations", [])
            ]

            bead_type_map = {v.value: v for v in BeadType}
            complexity_map = {v.value: v for v in Complexity}

            bead = DetailedBead(
                id=bead_id,
                title=rb.get("title", f"Bead {i}"),
                description=rb.get("description", ""),
                bead_type=bead_type_map.get(rb.get("bead_type", "code"), BeadType.CODE),
                file_operations=file_ops,
                shell_commands=rb.get("shell_commands", []),
                acceptance_criteria=rb.get("acceptance_criteria", []),
                estimated_complexity=complexity_map.get(
                    rb.get("estimated_complexity", "simple"), Complexity.SIMPLE,
                ),
            )
            beads.append(bead)

        raw_groups = parsed.get("parallel_groups", [])
        parallel_groups: list[list[str]] = []
        for group in raw_groups:
            resolved = [id_map[k] for k in group if k in id_map]
            if resolved:
                parallel_groups.append(resolved)

        if not parallel_groups:
            parallel_groups = [[b.id] for b in beads]

        graph = DetailedBeadGraph(
            mission_title=parsed.get("mission_title", ""),
            beads=beads,
            parallel_groups=parallel_groups,
            git_branch=parsed.get("git_branch", "feature/auto"),
        )
        return Success(graph)

    async def create_beads_in_tracker(
        self, graph: DetailedBeadGraph,
    ) -> dict[str, str]:
        """Создать задачи в bd, вернуть соответствие DetailedBead.id -> id задачи в трекере."""
        mapping: dict[str, str] = {}
        prev_bd_id: str | None = None

        for bead in graph.beads:
            try:
                cmd = [BD_CMD, "create", bead.title, "-p", "1", "-t", "task", "--json"]
                result = await anyio.run_process(cmd, cwd=self._root, check=False)

                if result.returncode == 0:
                    parsed_out = json.loads(result.stdout.decode())
                    bd_id = parsed_out.get("id", "")
                    if bd_id:
                        mapping[bead.id] = bd_id

                        if prev_bd_id:
                            await anyio.run_process(
                                [BD_CMD, "dep", "add", bd_id, prev_bd_id],
                                cwd=self._root, check=False,
                            )
                        prev_bd_id = bd_id
            except Exception:
                continue

        return mapping

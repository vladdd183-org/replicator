"""CLI-команды Replicator.

Главная команда: `replicator run` -- принимает URL репозитория и задачу,
клонирует, планирует через Opus, исполняет воркерами, создаёт PR.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any

import click
from returns.result import Failure, Success
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

console = Console()

BD_CMD = "/home/vladdd183/.local/bin/bd-wrapper"


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def _elapsed(start: float) -> str:
    s = time.monotonic() - start
    if s < 1:
        return f"{int(s * 1000)}ms"
    return f"{s:.1f}s"


def _get_llm_client() -> Any:
    from src.Ship.Configs import get_settings
    settings = get_settings()
    if not settings.openrouter_api_key:
        return None
    from openai import AsyncOpenAI
    return AsyncOpenAI(
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
    )


def _get_models() -> dict[str, str]:
    from src.Ship.Configs import get_settings
    settings = get_settings()
    return {
        "strategist": settings.strategist_model,
        "worker": settings.worker_model,
        "reviewer": settings.reviewer_model,
    }


def _agent_header(name: str, model: str, role: str) -> Panel:
    return Panel(
        f"[bold]{name}[/bold]  [dim]{model}[/dim]\n[dim]{role}[/dim]",
        border_style="cyan",
        expand=False,
    )


def _step(n: int, total: int, msg: str, model: str = "") -> None:
    m = f" [dim]({model})[/dim]" if model else ""
    console.print(f"\n[bold white on blue] {n}/{total} [/bold white on blue] {msg}{m}")


def _ok(msg: str) -> None:
    console.print(f"  [green]>[/green] {msg}")


def _warn(msg: str) -> None:
    console.print(f"  [yellow]![/yellow] {msg}")


def _info(msg: str) -> None:
    console.print(f"  [dim]  {msg}[/dim]")


def _fail(msg: str) -> None:
    console.print(f"  [red]x[/red] {msg}")


# ============================================================================
# `replicator run` -- главная команда
# ============================================================================

@click.group("replicator")
def replicator_group() -> None:
    """Replicator -- самоэволюционирующая система."""
    pass


@replicator_group.command("run")
@click.argument("repo_url")
@click.argument("intent")
@click.option("--dry-run", is_flag=True, help="Только планирование, без исполнения")
@click.option("--branch", default="", help="Имя ветки (авто если пусто)")
def run_cmd(repo_url: str, intent: str, dry_run: bool, branch: str) -> None:
    """Выполнить задачу на любом GitHub-репозитории.

    REPO_URL -- ссылка на GitHub репозиторий (https://github.com/owner/repo)
    INTENT   -- что нужно сделать

    Пример:
      replicator run https://github.com/vladdd183-org/replicator "Добавить rate limiter"
    """
    result = asyncio.run(_run_full_pipeline(repo_url, intent, dry_run=dry_run, branch_name=branch))
    if "error" in result:
        console.print(f"\n[bold red]ОШИБКА:[/bold red] {result['error']}")
        sys.exit(1)
    console.print(f"\n[dim]{json.dumps(result, ensure_ascii=False, indent=2)}[/dim]")


async def _run_full_pipeline(
    repo_url: str,
    intent: str,
    dry_run: bool = False,
    branch_name: str = "",
) -> dict[str, Any]:
    """Полный pipeline: clone -> plan -> beads -> execute -> PR."""

    from src.Containers.CoreSection.SpecModule.Actions.CompileSpecAction import CompileSpecAction
    from src.Containers.CoreSection.SpecModule.Actions.ValidateSpecAction import ValidateSpecAction
    from src.Containers.AgentSection.CompassModule.Actions.PlanMissionAction import PlanMissionAction
    from src.Containers.AgentSection.OrchestratorModule.Actions.ExecuteDetailedBeadAction import (
        ExecuteDetailedGraphAction,
    )
    from src.Containers.AgentSection.OrchestratorModule.Actions.FinalizeMissionAction import (
        FinalizeMissionAction,
    )

    llm = _get_llm_client()
    if llm is None:
        return {"error": "OPENROUTER_API_KEY не задан. Установите через .env или переменную окружения."}

    models = _get_models()
    pipeline_start = time.monotonic()

    # ── Header ────────────────────────────────────────────
    console.print()
    console.print(Rule("[bold cyan]REPLICATOR[/bold cyan]", style="cyan"))
    console.print()

    tree = Tree("[bold]Pipeline Config[/bold]")
    tree.add(f"[cyan]Стратег (мозг):[/cyan]  {models['strategist']}")
    tree.add(f"[green]Воркеры (руки):[/green]  {models['worker']}")
    tree.add(f"[yellow]Tracker:[/yellow]         Beads (bd CLI)")
    tree.add(f"[magenta]Repo:[/magenta]            {repo_url}")
    tree.add(f"[white]Intent:[/white]          {intent[:100]}")
    console.print(tree)
    console.print()

    # ── Detect local vs remote ────────────────────────────
    is_local = not repo_url.startswith("http")
    if is_local:
        project_root = repo_url
        _ok(f"Локальный проект: {project_root}")
    else:
        _step(0, 7, "Клонирование репозитория")
        project_root = await _clone_repo(repo_url)
        if not project_root:
            return {"error": f"Не удалось клонировать {repo_url}"}
        _ok(f"Клонирован в {project_root}")

    # ── Step 1: Compile ───────────────────────────────────
    _step(1, 7, "Компиляция intent", models["worker"])
    t0 = time.monotonic()
    compiler = CompileSpecAction(llm_client=llm, model=models["worker"])
    spec_result = await compiler.run(intent)
    if isinstance(spec_result, Failure):
        return {"error": f"Компиляция: {spec_result.failure()}"}

    spec = spec_result.unwrap()
    _ok(f"{spec.title}  [{_elapsed(t0)}]")
    _info(f"Тип: {spec.intent_type.value} | Приоритет: {spec.priority.value}")
    for ac in spec.acceptance_criteria[:3]:
        _info(f"AC: {ac[:90]}")

    # ── Step 2: Validate ──────────────────────────────────
    _step(2, 7, "Валидация MissionSpec")
    validator = ValidateSpecAction()
    valid_result = await validator.run(spec)
    if isinstance(valid_result, Failure):
        return {"error": f"Валидация: {valid_result.failure()}"}
    _ok("Spec валиден")

    # ── Step 3: Opus Plans ────────────────────────────────
    _step(3, 7, "OPUS планирует миссию", models["strategist"])
    console.print(_agent_header(
        "COMPASS Meta-Thinker",
        models["strategist"],
        "Анализирует проект, формирует детальный план с готовым кодом",
    ))
    t0 = time.monotonic()
    planner = PlanMissionAction(llm_client=llm, model=models["strategist"], project_root=project_root)
    plan_result = await planner.run(spec)
    if isinstance(plan_result, Failure):
        return {"error": f"Планирование: {plan_result.failure()}"}

    graph = plan_result.unwrap()
    total_ops = sum(len(b.file_operations) for b in graph.beads)

    _ok(f"Миссия: {graph.mission_title}  [{_elapsed(t0)}]")
    _ok(f"Branch: {branch_name or graph.git_branch}")
    _ok(f"Beads: {len(graph.beads)} | Файловых операций: {total_ops}")

    bead_table = Table(show_header=True, header_style="bold", expand=False, box=None, padding=(0, 2))
    bead_table.add_column("#", style="dim", width=3)
    bead_table.add_column("Bead", style="cyan")
    bead_table.add_column("Type", style="yellow", width=6)
    bead_table.add_column("Files", justify="right", width=5)
    bead_table.add_column("Cmds", justify="right", width=5)
    for i, b in enumerate(graph.beads):
        bead_table.add_row(str(i), b.title, b.bead_type.value, str(len(b.file_operations)), str(len(b.shell_commands)))
    console.print(bead_table)

    if branch_name:
        graph = graph.model_copy(update={"git_branch": branch_name})

    # ── Step 4: Create Beads in Tracker ───────────────────
    _step(4, 7, "Регистрация beads в трекере (bd)")
    t0 = time.monotonic()
    bd_mapping = await planner.create_beads_in_tracker(graph)
    _ok(f"Создано {len(bd_mapping)} beads  [{_elapsed(t0)}]")
    for detailed_id, bd_id in bd_mapping.items():
        bead = next((b for b in graph.beads if b.id == detailed_id), None)
        if bead:
            _info(f"{bd_id} -> {bead.title}")

    if dry_run:
        console.print()
        console.print(Rule("[yellow]DRY RUN -- исполнение пропущено[/yellow]", style="yellow"))

        for i, b in enumerate(graph.beads):
            console.print(f"\n  [bold cyan]bead-{i}: {b.title}[/bold cyan]")
            for op in b.file_operations:
                console.print(f"    [{op.action}] {op.file_path} ({len(op.content)} chars)")
            for cmd in b.shell_commands:
                console.print(f"    [shell] {cmd}")

        return {
            "status": "dry_run",
            "mission_title": graph.mission_title,
            "git_branch": graph.git_branch,
            "beads": len(graph.beads),
            "bd_beads": list(bd_mapping.values()),
            "file_operations": total_ops,
            "duration_ms": int((time.monotonic() - pipeline_start) * 1000),
        }

    # ── Step 5: Workers Execute ───────────────────────────
    _step(5, 7, "Воркеры исполняют bead-инструкции")
    console.print(_agent_header(
        "Worker Swarm",
        models["worker"],
        "bd claim -> запись файлов -> git commit -> bd close",
    ))
    t0 = time.monotonic()
    executor = ExecuteDetailedGraphAction(project_root=project_root, bd_bead_ids=bd_mapping)
    exec_result = await executor.run(graph)
    if isinstance(exec_result, Failure):
        return {"error": f"Исполнение: {exec_result.failure()}"}

    mission = exec_result.unwrap()
    _ok(f"Статус: {mission.overall_status}  [{_elapsed(t0)}]")
    _ok(f"Файлов: {mission.total_files_changed} | Коммитов: {mission.total_commits}")

    for r in mission.bead_results:
        bd_id = bd_mapping.get(r.bead_id, "")
        tag = f"[cyan]{bd_id}[/cyan] " if bd_id else ""
        if r.status == "success":
            _ok(f"{tag}{r.bead_title}  ({r.duration_ms}ms)")
            if r.commit_hash:
                _info(f"commit {r.commit_hash}")
            for f in r.files_written[:5]:
                _info(f"  {f}")
        else:
            _fail(f"{tag}{r.bead_title}: {r.error_message[:120]}")

    # ── Step 6: Finalize (push + PR) ─────────────────────
    finalize_info = mission.finalize or {}
    if finalize_info.get("url"):
        _step(6, 7, "Push + PR")
        _ok(f"PR: {finalize_info['url']}")
        _ok(f"Auto-merge: {'enabled' if finalize_info.get('auto_merge') else 'no'}")
    elif finalize_info.get("error"):
        _step(6, 7, "Push + PR")
        _warn(f"Финализация: {str(finalize_info['error'])[:200]}")
    else:
        _step(6, 7, "Push + PR")
        _warn("PR не создан (возможно нет прав или remote не настроен)")

    # ── Step 7: Summary ───────────────────────────────────
    _step(7, 7, "Итоги")
    total_time = int((time.monotonic() - pipeline_start) * 1000)

    summary = Table(show_header=False, expand=False, box=None, padding=(0, 2))
    summary.add_column("Key", style="bold")
    summary.add_column("Value")
    summary.add_row("Mission", mission.mission_title)
    summary.add_row("Branch", mission.git_branch)
    summary.add_row("Beads", f"{len(mission.bead_results)} executed")
    summary.add_row("Files", str(mission.total_files_changed))
    summary.add_row("Commits", str(mission.total_commits))
    summary.add_row("Duration", f"{total_time}ms ({total_time / 1000:.1f}s)")
    if finalize_info.get("url"):
        summary.add_row("PR", finalize_info["url"])
    console.print(summary)

    console.print()
    console.print(Rule("[bold green]DONE[/bold green]", style="green"))

    return {
        "status": mission.overall_status,
        "mission_title": mission.mission_title,
        "git_branch": mission.git_branch,
        "beads_executed": len(mission.bead_results),
        "bd_beads": list(bd_mapping.values()),
        "files_changed": mission.total_files_changed,
        "commits": mission.total_commits,
        "pr": finalize_info,
        "total_duration_ms": total_time,
    }


async def _clone_repo(repo_url: str) -> str:
    """Clone repo to /tmp/replicator-work/<owner>-<repo>."""
    import anyio

    parts = repo_url.rstrip("/").rstrip(".git").split("/")
    if len(parts) < 2:
        return ""
    name = f"{parts[-2]}-{parts[-1]}"
    target = f"/tmp/replicator-work/{name}"

    if os.path.exists(target):
        _info(f"Каталог существует, делаем git pull...")
        await anyio.run_process(["git", "pull", "--ff-only"], cwd=target, check=False)
        return target

    os.makedirs(os.path.dirname(target), exist_ok=True)
    result = await anyio.run_process(
        ["git", "clone", "--depth=1", repo_url, target],
        check=False,
    )
    if result.returncode != 0:
        return ""
    return target


# ============================================================================
# Legacy commands (сохранены для обратной совместимости)
# ============================================================================

@replicator_group.command("spec:compile")
@click.argument("intent")
def spec_compile_cmd(intent: str) -> None:
    """Скомпилировать intent в MissionSpec."""
    from src.Containers.CoreSection.SpecModule.Actions.CompileSpecAction import CompileSpecAction

    async def _compile() -> None:
        llm = _get_llm_client()
        models = _get_models()
        compiler = CompileSpecAction(llm_client=llm, model=models["worker"])
        result = await compiler.run(intent)
        if isinstance(result, Success):
            spec = result.unwrap()
            console.print(Panel("[bold green]MissionSpec[/bold green]", expand=False))
            console.print(json.dumps(spec.model_dump(), ensure_ascii=False, indent=2))
        else:
            console.print(f"[bold red]ОШИБКА:[/bold red] {result.failure()}")
            sys.exit(1)

    asyncio.run(_compile())


@replicator_group.command("cell:list")
def cell_list_cmd() -> None:
    """Показать все зарегистрированные Cell."""
    from src.Containers.CoreSection.CellRegistryModule.Actions.RegisterCellAction import _registry

    cells = list(_registry.values())
    if not cells:
        console.print("[dim]Нет зарегистрированных Cell[/dim]")
        return

    table = Table(title="Cell Registry")
    table.add_column("Name", style="cyan")
    table.add_column("Version")
    table.add_column("Section")
    table.add_column("Status", style="green")
    table.add_column("Hash", style="dim")
    for cell in cells:
        table.add_row(
            cell.name, cell.version, cell.section,
            cell.status.value,
            cell.spec_hash[:12] + "..." if cell.spec_hash else "-",
        )
    console.print(table)


@replicator_group.command("beads")
def beads_cmd() -> None:
    """Показать текущие beads в трекере."""
    import subprocess
    result = subprocess.run(
        [BD_CMD, "list", "--json"],
        capture_output=True, text=True, cwd=".",
    )
    if result.returncode != 0:
        console.print("[dim]bd не инициализирован или ошибка[/dim]")
        return
    try:
        items = json.loads(result.stdout)
    except json.JSONDecodeError:
        console.print("[dim]Нет beads[/dim]")
        return

    table = Table(title="Beads Tracker")
    table.add_column("ID", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("P", justify="center", width=2)
    table.add_column("Title")
    for item in items:
        table.add_row(
            item.get("id", ""),
            item.get("status", ""),
            str(item.get("priority", "")),
            item.get("title", ""),
        )
    console.print(table)

"""CLI-команды Replicator: evolve, generate, spec:compile, cell:list.

Точка входа для самоэволюции, генерации и работы с pipeline.
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

import click
from returns.result import Failure, Success
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def _get_llm_client() -> Any:
    """Создать OpenAI-совместимый клиент через OpenRouter."""
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
    """Получить конфигурацию моделей для разных ролей."""
    from src.Ship.Configs import get_settings
    settings = get_settings()
    return {
        "strategist": settings.strategist_model,
        "worker": settings.worker_model,
        "reviewer": settings.reviewer_model,
    }


async def _run_pipeline(intent: str, dry_run: bool = False) -> dict[str, Any]:
    """Полный pipeline: Intent -> Spec -> Strategy -> Beads -> Execute -> Verify.

    Мульти-модельная маршрутизация:
      - COMPASS (стратегия) -> Opus 4.6 (глубокое рассуждение)
      - Воркеры (компиляция, декомпозиция, исполнение) -> gpt-oss-120b (Cerebras, 569+ tok/s)
    """
    from src.Containers.CoreSection.SpecModule.Actions.CompileSpecAction import CompileSpecAction
    from src.Containers.CoreSection.SpecModule.Actions.ValidateSpecAction import ValidateSpecAction
    from src.Containers.AgentSection.CompassModule.Actions.StrategizeAction import StrategizeAction
    from src.Containers.AgentSection.MakerModule.Actions.DecomposeAction import DecomposeAction
    from src.Containers.AgentSection.OrchestratorModule.Actions.ExecuteBeadGraphAction import (
        ExecuteBeadGraphAction,
    )
    from src.Containers.CoreSection.EvolutionModule.Actions.VerifyAction import VerifyAction

    llm = _get_llm_client()
    models = _get_models()

    console.print(Panel("[bold cyan]REPLICATOR PIPELINE[/bold cyan]", expand=False))
    console.print(f"  [dim]Стратег:  {models['strategist']}[/dim]")
    console.print(f"  [dim]Воркер:   {models['worker']}[/dim]")
    console.print(f"  [dim]Ревьюер:  {models['reviewer']}[/dim]")

    # 1. Compile (worker -- быстрая модель)
    console.print("\n[bold]1/6[/bold] Компиляция intent -> MissionSpec [dim]({m})[/dim]...".format(m=models["worker"]))
    compiler = CompileSpecAction(llm_client=llm, model=models["worker"])
    spec_result = await compiler.run(intent)
    if isinstance(spec_result, Failure):
        return {"error": f"Compilation failed: {spec_result.failure()}"}

    spec = spec_result.unwrap()
    console.print(f"  [green]✓[/green] {spec.title} ({spec.intent_type.value})")

    # 2. Validate
    console.print("\n[bold]2/6[/bold] Валидация MissionSpec...")
    validator = ValidateSpecAction()
    valid_result = await validator.run(spec)
    if isinstance(valid_result, Failure):
        return {"error": f"Validation failed: {valid_result.failure()}"}
    console.print("  [green]✓[/green] Spec валиден")

    # 3. Strategize (strategist -- Opus 4.6, самая мощная модель)
    console.print("\n[bold]3/6[/bold] Формирование стратегии (COMPASS) [dim]({m})[/dim]...".format(m=models["strategist"]))
    strategist = StrategizeAction(llm_client=llm, model=models["strategist"])
    strat_result = await strategist.run(spec)
    if isinstance(strat_result, Failure):
        return {"error": f"Strategy failed: {strat_result.failure()}"}

    strategy = strat_result.unwrap()
    console.print(f"  [green]✓[/green] Подход: {strategy.approach[:100]}")
    console.print(f"  [green]✓[/green] Фаз: {len(strategy.phases)}, уверенность: {strategy.confidence:.0%}")

    # 4. Decompose (worker -- быстрая модель)
    console.print("\n[bold]4/6[/bold] Декомпозиция на Beads (MAKER) [dim]({m})[/dim]...".format(m=models["worker"]))
    decomposer = DecomposeAction(llm_client=llm, model=models["worker"])
    bead_result = await decomposer.run(strategy)
    if isinstance(bead_result, Failure):
        return {"error": f"Decomposition failed: {bead_result.failure()}"}

    bead_graph = bead_result.unwrap()
    console.print(f"  [green]✓[/green] Beads: {len(bead_graph.beads)}")
    for b in bead_graph.beads:
        console.print(f"    - [{b.bead_type.value}] {b.title}")

    if dry_run:
        console.print("\n[yellow]DRY RUN -- исполнение пропущено[/yellow]")
        return {
            "status": "dry_run",
            "spec": spec.model_dump(),
            "strategy": strategy.model_dump(),
            "beads": len(bead_graph.beads),
        }

    # 5. Execute (worker -- быстрая модель, массовый параллелизм)
    console.print("\n[bold]5/6[/bold] Исполнение BeadGraph (Orchestrator) [dim]({m})[/dim]...".format(m=models["worker"]))
    executor = ExecuteBeadGraphAction(llm_client=llm, model=models["worker"])
    exec_result = await executor.run(bead_graph)
    if isinstance(exec_result, Failure):
        return {"error": f"Execution failed: {exec_result.failure()}"}

    execution = exec_result.unwrap()
    console.print(f"  [green]✓[/green] Статус: {execution.overall_status}")
    console.print(f"  [green]✓[/green] Время: {execution.total_duration_ms}ms")

    # 6. Verify
    console.print("\n[bold]6/6[/bold] Верификация (Evolution)...")
    verifier = VerifyAction()
    verify_result = await verifier.run(execution)
    if isinstance(verify_result, Failure):
        evidence_err = verify_result.failure()
        console.print(f"  [yellow]![/yellow] Верификация: {evidence_err.message[:100]}")
        from src.Containers.CoreSection.SpecModule.Data.Schemas.Models import EvidenceBundle
        evidence = EvidenceBundle(status="needs_review", reviewer_notes=[evidence_err.message])
    else:
        evidence = verify_result.unwrap()
    console.print(f"  [green]✓[/green] Верификация: {evidence.status}")

    console.print(Panel("[bold green]PIPELINE ЗАВЕРШЁН[/bold green]", expand=False))

    return {
        "status": evidence.status,
        "spec_title": spec.title,
        "beads_executed": len(execution.bead_results),
        "total_duration_ms": execution.total_duration_ms,
    }


@click.group("replicator")
def replicator_group() -> None:
    """Replicator -- самоэволюционирующая система."""
    pass


@replicator_group.command("evolve")
@click.argument("intent")
@click.option("--dry-run", is_flag=True, help="Только план, без исполнения")
def evolve_cmd(intent: str, dry_run: bool) -> None:
    """Запустить pipeline самоэволюции.

    INTENT -- текстовое описание задачи.
    """
    result = asyncio.run(_run_pipeline(intent, dry_run=dry_run))

    if "error" in result:
        console.print(f"\n[bold red]ОШИБКА:[/bold red] {result['error']}")
        sys.exit(1)

    console.print(f"\n[dim]{json.dumps(result, ensure_ascii=False, indent=2)}[/dim]")


@replicator_group.command("spec:compile")
@click.argument("intent")
def spec_compile_cmd(intent: str) -> None:
    """Скомпилировать intent в MissionSpec (без исполнения)."""
    from src.Containers.CoreSection.SpecModule.Actions.CompileSpecAction import CompileSpecAction

    async def _compile() -> None:
        llm = _get_llm_client()
        compiler = CompileSpecAction(llm_client=llm)
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
            cell.name,
            cell.version,
            cell.section,
            cell.status.value,
            cell.spec_hash[:12] + "..." if cell.spec_hash else "-",
        )

    console.print(table)


@replicator_group.command("generate")
@click.argument("intent")
@click.option("--dry-run", is_flag=True, help="Только план")
def generate_cmd(intent: str, dry_run: bool) -> None:
    """Сгенерировать новый проект из intent."""
    full_intent = f"[generate] {intent}"
    result = asyncio.run(_run_pipeline(full_intent, dry_run=dry_run))

    if "error" in result:
        console.print(f"\n[bold red]ОШИБКА:[/bold red] {result['error']}")
        sys.exit(1)

    console.print(f"\n[dim]{json.dumps(result, ensure_ascii=False, indent=2)}[/dim]")


@replicator_group.command("evolve2")
@click.argument("intent")
@click.option("--dry-run", is_flag=True, help="Только план Opus, без исполнения")
def evolve2_cmd(intent: str, dry_run: bool) -> None:
    """V2 Pipeline: Opus думает, воркеры исполняют.

    Opus 4.6 анализирует проект, создаёт детальный план с готовым кодом.
    Воркеры (gpt-oss-120b) НЕ думают -- просто записывают файлы.

    INTENT -- текстовое описание задачи.
    """
    result = asyncio.run(_run_pipeline_v2(intent, dry_run=dry_run))

    if "error" in result:
        console.print(f"\n[bold red]ОШИБКА:[/bold red] {result['error']}")
        sys.exit(1)

    console.print(f"\n[dim]{json.dumps(result, ensure_ascii=False, indent=2)}[/dim]")


async def _run_pipeline_v2(intent: str, dry_run: bool = False) -> dict[str, Any]:
    """V2 Pipeline: Opus = мозг, Workers = руки.
    
    1. Opus компилирует intent в MissionSpec (быстрая модель)
    2. Opus анализирует проект и создаёт DetailedBeadGraph с ГОТОВЫМ КОДОМ
    3. Воркеры механически записывают файлы и коммитят
    """
    from src.Containers.CoreSection.SpecModule.Actions.CompileSpecAction import CompileSpecAction
    from src.Containers.CoreSection.SpecModule.Actions.ValidateSpecAction import ValidateSpecAction
    from src.Containers.AgentSection.CompassModule.Actions.PlanMissionAction import PlanMissionAction
    from src.Containers.AgentSection.OrchestratorModule.Actions.ExecuteDetailedBeadAction import (
        ExecuteDetailedGraphAction,
    )
    
    from src.Ship.Configs import get_settings
    settings = get_settings()

    llm = _get_llm_client()
    if llm is None:
        return {"error": "OPENROUTER_API_KEY not set"}

    console.print(Panel(
        "[bold cyan]REPLICATOR V2 PIPELINE[/bold cyan]\n"
        "[dim]Opus = мозг (думает) | Workers = руки (делают)[/dim]",
        expand=False,
    ))
    console.print(f"  [dim]Стратег (Opus):  {settings.strategist_model}[/dim]")
    console.print(f"  [dim]Воркер:          gpt-oss-120b (запись файлов)[/dim]")

    import time
    pipeline_start = time.monotonic()

    # 1. Compile spec (быстрая модель)
    console.print("\n[bold]1/4[/bold] Компиляция intent [dim]({m})[/dim]...".format(m=settings.worker_model))
    compiler = CompileSpecAction(llm_client=llm, model=settings.worker_model)
    spec_result = await compiler.run(intent)
    if isinstance(spec_result, Failure):
        return {"error": f"Compilation failed: {spec_result.failure()}"}
    spec = spec_result.unwrap()
    console.print(f"  [green]✓[/green] {spec.title}")
    console.print(f"  [dim]  Тип: {spec.intent_type.value} | Приоритет: {spec.priority.value}[/dim]")
    if spec.acceptance_criteria:
        for ac in spec.acceptance_criteria[:3]:
            console.print(f"  [dim]  AC: {ac[:80]}[/dim]")

    # 2. Validate
    console.print("\n[bold]2/4[/bold] Валидация...")
    validator = ValidateSpecAction()
    valid_result = await validator.run(spec)
    if isinstance(valid_result, Failure):
        return {"error": f"Validation failed: {valid_result.failure()}"}
    console.print("  [green]✓[/green] Spec валиден")

    # 3. Opus планирует ДЕТАЛЬНО (это главный шаг!)
    console.print("\n[bold]3/4[/bold] OPUS планирует миссию [dim]({m})[/dim]...".format(m=settings.strategist_model))
    console.print("  [dim]  Анализ проекта, генерация кода, формирование bead-инструкций...[/dim]")
    planner = PlanMissionAction(llm_client=llm, model=settings.strategist_model)
    plan_result = await planner.run(spec)
    if isinstance(plan_result, Failure):
        return {"error": f"Planning failed: {plan_result.failure()}"}

    graph = plan_result.unwrap()
    console.print(f"  [green]✓[/green] Миссия: {graph.mission_title}")
    console.print(f"  [green]✓[/green] Git branch: {graph.git_branch}")
    console.print(f"  [green]✓[/green] Beads: {len(graph.beads)}")
    
    total_ops = sum(len(b.file_operations) for b in graph.beads)
    console.print(f"  [green]✓[/green] Файловых операций: {total_ops}")
    
    for i, b in enumerate(graph.beads):
        n_ops = len(b.file_operations)
        n_cmds = len(b.shell_commands)
        console.print(f"    [cyan]bead-{i}[/cyan] [{b.bead_type.value}] {b.title} ({n_ops} files, {n_cmds} cmds)")

    if dry_run:
        console.print("\n[yellow]DRY RUN -- исполнение пропущено[/yellow]")
        console.print("\n[bold]Детали bead-инструкций:[/bold]")
        for i, b in enumerate(graph.beads):
            console.print(f"\n  [bold cyan]bead-{i}: {b.title}[/bold cyan]")
            for op in b.file_operations:
                size = len(op.content)
                console.print(f"    [{op.action}] {op.file_path} ({size} chars)")
            for cmd in b.shell_commands:
                console.print(f"    [shell] {cmd}")
        
        return {
            "status": "dry_run",
            "mission_title": graph.mission_title,
            "git_branch": graph.git_branch,
            "beads": len(graph.beads),
            "file_operations": total_ops,
            "duration_planning_ms": int((time.monotonic() - pipeline_start) * 1000),
        }

    # 4. Workers исполняют (просто пишут файлы)
    console.print("\n[bold]4/4[/bold] Воркеры исполняют bead-инструкции...")
    executor = ExecuteDetailedGraphAction()
    exec_result = await executor.run(graph)
    if isinstance(exec_result, Failure):
        return {"error": f"Execution failed: {exec_result.failure()}"}

    mission_result = exec_result.unwrap()
    console.print(f"  [green]✓[/green] Статус: {mission_result.overall_status}")
    console.print(f"  [green]✓[/green] Файлов изменено: {mission_result.total_files_changed}")
    console.print(f"  [green]✓[/green] Коммитов: {mission_result.total_commits}")
    console.print(f"  [green]✓[/green] Ветка: {mission_result.git_branch}")
    console.print(f"  [green]✓[/green] Время: {mission_result.total_duration_ms}ms")

    for r in mission_result.bead_results:
        status_icon = "[green]✓[/green]" if r.status == "success" else "[red]✗[/red]"
        console.print(f"    {status_icon} {r.bead_title} ({len(r.files_written)} files, {r.duration_ms}ms)")
        if r.commit_hash:
            console.print(f"      [dim]commit: {r.commit_hash}[/dim]")

    total_time = int((time.monotonic() - pipeline_start) * 1000)
    console.print(Panel(f"[bold green]PIPELINE V2 ЗАВЕРШЁН за {total_time}ms[/bold green]", expand=False))

    return {
        "status": mission_result.overall_status,
        "mission_title": mission_result.mission_title,
        "git_branch": mission_result.git_branch,
        "beads_executed": len(mission_result.bead_results),
        "files_changed": mission_result.total_files_changed,
        "commits": mission_result.total_commits,
        "total_duration_ms": total_time,
    }


@replicator_group.command("evolve3")
@click.argument("intent")
@click.option("--dry-run", is_flag=True, help="Только план Opus + создание beads, без исполнения")
def evolve3_cmd(intent: str, dry_run: bool) -> None:
    """V3 Pipeline: Opus + Beads + GitHub Flow.

    Opus 4.6 планирует, создаёт реальные beads в bd tracker.
    Воркеры claim/execute/close beads. В конце -- PR на GitHub.

    INTENT -- текстовое описание задачи.
    """
    result = asyncio.run(_run_pipeline_v3(intent, dry_run=dry_run))

    if "error" in result:
        console.print(f"\n[bold red]ОШИБКА:[/bold red] {result['error']}")
        sys.exit(1)

    console.print(f"\n[dim]{json.dumps(result, ensure_ascii=False, indent=2)}[/dim]")


async def _run_pipeline_v3(intent: str, dry_run: bool = False) -> dict[str, Any]:
    """V3 Pipeline: Opus + Beads (bd) + GitHub Flow.

    1. Compile intent -> MissionSpec (fast model)
    2. Validate
    3. Opus plans mission with detailed file operations
    4. Create real beads in bd tracker
    5. Workers: claim bead -> write files -> git commit -> close bead
    6. Finalize: git push -> PR -> auto-merge
    """
    from src.Containers.CoreSection.SpecModule.Actions.CompileSpecAction import CompileSpecAction
    from src.Containers.CoreSection.SpecModule.Actions.ValidateSpecAction import ValidateSpecAction
    from src.Containers.AgentSection.CompassModule.Actions.PlanMissionAction import PlanMissionAction
    from src.Containers.AgentSection.OrchestratorModule.Actions.ExecuteDetailedBeadAction import (
        ExecuteDetailedGraphAction,
    )
    from src.Containers.AgentSection.OrchestratorModule.Actions.FinalizeMissionAction import (
        FinalizeMissionAction,
    )

    from src.Ship.Configs import get_settings
    settings = get_settings()

    llm = _get_llm_client()
    if llm is None:
        return {"error": "OPENROUTER_API_KEY not set"}

    models = _get_models()

    console.print(Panel(
        "[bold cyan]REPLICATOR V3 PIPELINE[/bold cyan]\n"
        "[dim]Opus + Beads (bd) + GitHub Flow[/dim]",
        expand=False,
    ))
    console.print(f"  [dim]Стратег:  {models['strategist']}[/dim]")
    console.print(f"  [dim]Tracker:  Beads (bd CLI)[/dim]")
    console.print(f"  [dim]Git:      branch -> commits -> PR -> merge queue[/dim]")

    import time as _time
    pipeline_start = _time.monotonic()

    # 1. Compile spec
    console.print("\n[bold]1/6[/bold] Компиляция intent [dim]({m})[/dim]...".format(m=models["worker"]))
    compiler = CompileSpecAction(llm_client=llm, model=models["worker"])
    spec_result = await compiler.run(intent)
    if isinstance(spec_result, Failure):
        return {"error": f"Compilation failed: {spec_result.failure()}"}
    spec = spec_result.unwrap()
    console.print(f"  [green]✓[/green] {spec.title}")

    # 2. Validate
    console.print("\n[bold]2/6[/bold] Валидация...")
    validator = ValidateSpecAction()
    valid_result = await validator.run(spec)
    if isinstance(valid_result, Failure):
        return {"error": f"Validation failed: {valid_result.failure()}"}
    console.print("  [green]✓[/green] Spec валиден")

    # 3. Opus plans mission
    console.print("\n[bold]3/6[/bold] OPUS планирует миссию [dim]({m})[/dim]...".format(m=models["strategist"]))
    planner = PlanMissionAction(llm_client=llm, model=models["strategist"])
    plan_result = await planner.run(spec)
    if isinstance(plan_result, Failure):
        return {"error": f"Planning failed: {plan_result.failure()}"}

    graph = plan_result.unwrap()
    total_ops = sum(len(b.file_operations) for b in graph.beads)
    console.print(f"  [green]✓[/green] Миссия: {graph.mission_title}")
    console.print(f"  [green]✓[/green] Branch: {graph.git_branch}")
    console.print(f"  [green]✓[/green] Beads: {len(graph.beads)}, Files: {total_ops}")

    # 4. Create beads in bd tracker
    console.print("\n[bold]4/6[/bold] Создание beads в bd tracker...")
    bd_mapping = await planner.create_beads_in_tracker(graph)
    console.print(f"  [green]✓[/green] Создано beads: {len(bd_mapping)}")
    for detailed_id, bd_id in bd_mapping.items():
        bead = next((b for b in graph.beads if b.id == detailed_id), None)
        if bead:
            console.print(f"    [cyan]{bd_id}[/cyan] {bead.title}")

    if dry_run:
        console.print("\n[yellow]DRY RUN -- исполнение пропущено[/yellow]")
        return {
            "status": "dry_run",
            "mission_title": graph.mission_title,
            "git_branch": graph.git_branch,
            "beads": len(graph.beads),
            "bd_beads": list(bd_mapping.values()),
            "file_operations": total_ops,
        }

    # 5. Workers execute (claim -> write -> commit -> close)
    console.print("\n[bold]5/6[/bold] Воркеры исполняют (bd claim -> файлы -> git commit -> bd close)...")
    executor = ExecuteDetailedGraphAction(bd_bead_ids=bd_mapping)
    exec_result = await executor.run(graph)
    if isinstance(exec_result, Failure):
        return {"error": f"Execution failed: {exec_result.failure()}"}

    mission_result = exec_result.unwrap()
    console.print(f"  [green]✓[/green] Статус: {mission_result.overall_status}")
    console.print(f"  [green]✓[/green] Файлов: {mission_result.total_files_changed}")
    console.print(f"  [green]✓[/green] Коммитов: {mission_result.total_commits}")

    for r in mission_result.bead_results:
        icon = "[green]✓[/green]" if r.status == "success" else "[red]✗[/red]"
        bd_id = bd_mapping.get(r.bead_id, "")
        label = f"({bd_id}) " if bd_id else ""
        console.print(f"    {icon} {label}{r.bead_title} ({r.duration_ms}ms)")

    # 6. Finalize: push + PR + auto-merge
    console.print("\n[bold]6/6[/bold] Финализация: push -> PR -> auto-merge...")
    finalizer = FinalizeMissionAction()
    final_result = await finalizer.run(mission_result)

    if isinstance(final_result, Failure):
        console.print(f"  [yellow]![/yellow] Финализация: {final_result.failure().message[:200]}")
        pr_info = {}
    else:
        pr_info = final_result.unwrap()
        if pr_info.get("pr_url"):
            console.print(f"  [green]✓[/green] PR: {pr_info['pr_url']}")
            console.print(f"  [green]✓[/green] Auto-merge: {'enabled' if pr_info.get('auto_merge') else 'disabled'}")
        else:
            console.print(f"  [yellow]![/yellow] PR создание: {pr_info}")

    total_time = int((_time.monotonic() - pipeline_start) * 1000)
    console.print(Panel(f"[bold green]PIPELINE V3 ЗАВЕРШЁН за {total_time}ms[/bold green]", expand=False))

    return {
        "status": mission_result.overall_status,
        "mission_title": mission_result.mission_title,
        "git_branch": mission_result.git_branch,
        "beads_executed": len(mission_result.bead_results),
        "bd_beads": list(bd_mapping.values()),
        "files_changed": mission_result.total_files_changed,
        "commits": mission_result.total_commits,
        "pr": pr_info,
        "total_duration_ms": total_time,
    }

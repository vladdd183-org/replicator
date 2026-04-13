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


async def _run_pipeline(intent: str, dry_run: bool = False) -> dict[str, Any]:
    """Полный pipeline: Intent -> Spec -> Strategy -> Beads -> Execute -> Verify."""
    from src.Containers.CoreSection.SpecModule.Actions.CompileSpecAction import CompileSpecAction
    from src.Containers.CoreSection.SpecModule.Actions.ValidateSpecAction import ValidateSpecAction
    from src.Containers.AgentSection.CompassModule.Actions.StrategizeAction import StrategizeAction
    from src.Containers.AgentSection.MakerModule.Actions.DecomposeAction import DecomposeAction
    from src.Containers.AgentSection.OrchestratorModule.Actions.ExecuteBeadGraphAction import (
        ExecuteBeadGraphAction,
    )
    from src.Containers.CoreSection.EvolutionModule.Actions.VerifyAction import VerifyAction

    llm = _get_llm_client()

    console.print(Panel("[bold cyan]REPLICATOR PIPELINE[/bold cyan]", expand=False))

    # 1. Compile
    console.print("\n[bold]1/6[/bold] Компиляция intent -> MissionSpec...")
    compiler = CompileSpecAction(llm_client=llm)
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

    # 3. Strategize
    console.print("\n[bold]3/6[/bold] Формирование стратегии (COMPASS)...")
    strategist = StrategizeAction(llm_client=llm)
    strat_result = await strategist.run(spec)
    if isinstance(strat_result, Failure):
        return {"error": f"Strategy failed: {strat_result.failure()}"}

    strategy = strat_result.unwrap()
    console.print(f"  [green]✓[/green] Подход: {strategy.approach[:100]}")
    console.print(f"  [green]✓[/green] Фаз: {len(strategy.phases)}, уверенность: {strategy.confidence:.0%}")

    # 4. Decompose
    console.print("\n[bold]4/6[/bold] Декомпозиция на Beads (MAKER)...")
    decomposer = DecomposeAction(llm_client=llm)
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

    # 5. Execute
    console.print("\n[bold]5/6[/bold] Исполнение BeadGraph (Orchestrator)...")
    executor = ExecuteBeadGraphAction(llm_client=llm)
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

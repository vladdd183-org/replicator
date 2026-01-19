"""CLI command for generating Porto Tasks.

Usage:
    porto make:task SendEmail --module=Notification
    porto make:task HashPassword --module=User --sync
"""

import click
from rich.console import Console
from rich.panel import Panel

from src.Ship.CLI.Generator import generate_component, to_pascal_case

console = Console()


@click.command("make:task")
@click.argument("name")
@click.option(
    "--module",
    "-m",
    required=True,
    help="Target module name (e.g., User, Blog)",
)
@click.option(
    "--section",
    "-s",
    default="AppSection",
    help="Section name (default: AppSection)",
)
@click.option(
    "--sync",
    "is_sync",
    is_flag=True,
    help="Create synchronous task (for CPU-bound operations)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite if file exists",
)
def make_task(
    name: str,
    module: str,
    section: str,
    is_sync: bool,
    force: bool,
) -> None:
    """Generate a new Task (atomic operation) for a module.
    
    Tasks are atomic, reusable operations shared between Actions.
    They hold business logic that can be reused across modules.
    
    \b
    Task types:
    - Async Task (default): For I/O operations (API calls, DB, email)
    - Sync Task (--sync): For CPU-bound operations (hashing, calculations)
    
    \b
    Naming convention:
    - Start with a verb: Send, Generate, Hash, Calculate, etc.
    - "Task" suffix is added automatically
    
    \b
    Examples:
        porto make:task SendEmail --module=Notification
        porto make:task HashPassword --module=User --sync
        porto make:task GenerateToken --module=Auth
        porto make:task CalculateDiscount --module=Order --sync
    """
    # Normalize names
    name = to_pascal_case(name)
    module = to_pascal_case(module)
    
    # Remove "Task" suffix if provided
    if name.endswith("Task"):
        name = name[:-4]
    
    task_type = "sync_task" if is_sync else "task"
    task_type_label = "SyncTask" if is_sync else "Task"
    
    console.print(Panel.fit(
        f"[bold cyan]Task Generator[/bold cyan]\n\n"
        f"[white]Task:[/white] [green]{name}Task[/green]\n"
        f"[white]Type:[/white] [green]{task_type_label}[/green]\n"
        f"[white]Module:[/white] [green]{module}Module[/green]\n"
        f"[white]Section:[/white] [green]{section}[/green]",
        title="[bold]Generating Task[/bold]",
        border_style="blue",
    ))
    
    try:
        generated = generate_component(
            component_type=task_type,
            component_name=name,
            module_name=module,
            section=section,
        )
        
        if generated:
            console.print(f"\n[bold green]Success![/bold green] Task created.")
            _print_next_steps(name, module, section, is_sync)
        else:
            console.print("\n[yellow]Task was not created.[/yellow]")
            if not force:
                console.print("[dim]File may already exist. Use --force to overwrite.[/dim]")
                
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        raise SystemExit(1)


def _print_next_steps(name: str, module: str, section: str, is_sync: bool) -> None:
    """Print next steps after task generation."""
    task_path = f"src/Containers/{section}/{module}Module/Tasks/{name}Task.py"
    
    usage_example = (
        f"# In Action (async context):\n"
        f"   result = await anyio.to_thread.run_sync(self.{name.lower()}_task.run, data)"
        if is_sync else
        f"# In Action:\n"
        f"   result = await self.{name.lower()}_task.run(data)"
    )
    
    console.print(Panel.fit(
        f"[bold]Next steps:[/bold]\n\n"
        f"1. [cyan]Implement the task logic:[/cyan]\n"
        f"   {task_path}\n\n"
        f"2. [cyan]Register in Providers.py (APP scope):[/cyan]\n"
        f"   {name.lower()}_task = provide({name}Task)\n\n"
        f"3. [cyan]Usage example:[/cyan]\n"
        f"   {usage_example}",
        title="[bold green]What's Next?[/bold green]",
        border_style="green",
    ))

"""CLI command for generating Porto Actions.

Usage:
    porto make:action CreatePost --module=Blog
    porto make:action PublishArticle --module=Blog --section=ContentSection
"""

import click
from rich.console import Console
from rich.panel import Panel

from src.Ship.CLI.Generator import generate_component, to_pascal_case

console = Console()


@click.command("make:action")
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
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite if file exists",
)
def make_action(
    name: str,
    module: str,
    section: str,
    force: bool,
) -> None:
    """Generate a new Action (Use Case) for a module.
    
    Actions represent Use Cases of the application.
    They orchestrate Tasks and always return Result[T, E].
    
    \b
    Naming convention:
    - Start with a verb: Create, Update, Delete, Publish, etc.
    - End with entity name if applicable
    - "Action" suffix is added automatically
    
    \b
    Examples:
        porto make:action CreatePost --module=Blog
        porto make:action PublishArticle --module=Blog
        porto make:action SendNotification --module=Notification
    """
    # Normalize names
    name = to_pascal_case(name)
    module = to_pascal_case(module)
    
    # Remove "Action" suffix if provided
    if name.endswith("Action"):
        name = name[:-6]
    
    console.print(Panel.fit(
        f"[bold cyan]Action Generator[/bold cyan]\n\n"
        f"[white]Action:[/white] [green]{name}Action[/green]\n"
        f"[white]Module:[/white] [green]{module}Module[/green]\n"
        f"[white]Section:[/white] [green]{section}[/green]",
        title="[bold]Generating Action[/bold]",
        border_style="blue",
    ))
    
    try:
        generated = generate_component(
            component_type="action",
            component_name=name,
            module_name=module,
            section=section,
        )
        
        if generated:
            console.print(f"\n[bold green]Success![/bold green] Action created.")
            _print_next_steps(name, module, section)
        else:
            console.print("\n[yellow]Action was not created.[/yellow]")
            if not force:
                console.print("[dim]File may already exist. Use --force to overwrite.[/dim]")
                
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        raise SystemExit(1)


def _print_next_steps(name: str, module: str, section: str) -> None:
    """Print next steps after action generation."""
    action_path = f"src/Containers/{section}/{module}Module/Actions/{name}Action.py"
    
    console.print(Panel.fit(
        f"[bold]Next steps:[/bold]\n\n"
        f"1. [cyan]Implement the action logic:[/cyan]\n"
        f"   {action_path}\n\n"
        f"2. [cyan]Register in Providers.py:[/cyan]\n"
        f"   {name.lower()}_action = provide({name}Action)\n\n"
        f"3. [cyan]Add endpoint in Controller (if needed):[/cyan]\n"
        f"   @post('/{name.lower()}')\n"
        f"   @result_handler(ResponseDTO, success_status=201)\n"
        f"   async def {name.lower()}(self, action: FromDishka[{name}Action]) -> Result:",
        title="[bold green]What's Next?[/bold green]",
        border_style="green",
    ))

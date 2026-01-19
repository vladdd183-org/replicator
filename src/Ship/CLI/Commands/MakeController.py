"""CLI command for generating Porto Controllers.

Usage:
    porto make:controller Admin --module=User
    porto make:controller Payment --module=Order
"""

import click
from rich.console import Console
from rich.panel import Panel

from src.Ship.CLI.Generator import generate_component, to_pascal_case

console = Console()


@click.command("make:controller")
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
def make_controller(
    name: str,
    module: str,
    section: str,
    force: bool,
) -> None:
    """Generate a new HTTP Controller for a module.
    
    Controllers handle HTTP requests and delegate to Actions/Queries.
    They don't contain business logic - only HTTP concerns.
    
    \b
    Controller rules:
    - Use @result_handler for write operations (POST, PATCH, DELETE)
    - Return DTO directly for read operations (GET)
    - Inject Actions/Queries via FromDishka
    - One Controller can have multiple endpoints
    
    \b
    Examples:
        porto make:controller Admin --module=User
        porto make:controller Payment --module=Order
        porto make:controller Search --module=Product
    """
    # Normalize names
    name = to_pascal_case(name)
    module = to_pascal_case(module)
    
    # Remove "Controller" suffix if provided
    if name.endswith("Controller"):
        name = name[:-10]
    
    console.print(Panel.fit(
        f"[bold cyan]Controller Generator[/bold cyan]\n\n"
        f"[white]Controller:[/white] [green]{name}Controller[/green]\n"
        f"[white]Module:[/white] [green]{module}Module[/green]\n"
        f"[white]Section:[/white] [green]{section}[/green]",
        title="[bold]Generating Controller[/bold]",
        border_style="blue",
    ))
    
    try:
        generated = generate_component(
            component_type="controller",
            component_name=name,
            module_name=module,
            section=section,
        )
        
        if generated:
            console.print(f"\n[bold green]Success![/bold green] Controller created.")
            _print_next_steps(name, module, section)
        else:
            console.print("\n[yellow]Controller was not created.[/yellow]")
            if not force:
                console.print("[dim]File may already exist. Use --force to overwrite.[/dim]")
                
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        raise SystemExit(1)


def _print_next_steps(name: str, module: str, section: str) -> None:
    """Print next steps after controller generation."""
    controller_path = f"src/Containers/{section}/{module}Module/UI/API/Controllers/{name}Controller.py"
    
    console.print(Panel.fit(
        f"[bold]Next steps:[/bold]\n\n"
        f"1. [cyan]Add endpoints to the controller:[/cyan]\n"
        f"   {controller_path}\n\n"
        f"2. [cyan]Register routes in Routes.py:[/cyan]\n"
        f"   from .Controllers.{name}Controller import {name}Controller\n"
        f"   route_handlers = [..., {name}Controller]\n\n"
        f"3. [cyan]Add to main app router (if new route group):[/cyan]\n"
        f"   # In src/App.py\n"
        f"   from src.Containers.{section}.{module}Module.UI.API.Routes import router",
        title="[bold green]What's Next?[/bold green]",
        border_style="green",
    ))

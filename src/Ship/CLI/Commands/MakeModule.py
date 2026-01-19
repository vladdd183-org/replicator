"""CLI command for generating Porto modules.

Usage:
    porto make:module Blog
    porto make:module Product --section=ShopSection
    porto make:module Order --with-graphql --with-websocket
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.Ship.CLI.Generator import generate_module, to_pascal_case

console = Console()


@click.command("make:module")
@click.argument("name")
@click.option(
    "--section",
    "-s",
    default="AppSection",
    help="Section name (default: AppSection)",
)
@click.option(
    "--with-graphql",
    is_flag=True,
    help="Include GraphQL resolvers and types",
)
@click.option(
    "--with-websocket",
    is_flag=True,
    help="Include WebSocket handlers",
)
@click.option(
    "--with-cli",
    is_flag=True,
    help="Include CLI commands",
)
@click.option(
    "--with-workers",
    is_flag=True,
    help="Include TaskIQ background workers",
)
@click.option(
    "--all",
    "with_all",
    is_flag=True,
    help="Include all optional features (GraphQL, WebSocket, CLI, Workers)",
)
def make_module(
    name: str,
    section: str,
    with_graphql: bool,
    with_websocket: bool,
    with_cli: bool,
    with_workers: bool,
    with_all: bool,
) -> None:
    """Generate a complete Porto module with full structure.
    
    Creates a new module in src/Containers/{section}/{name}Module/ with:
    
    \b
    - Actions (Create, Update, Delete)
    - Queries (Get, List) 
    - Data (Repository, Schemas, UnitOfWork)
    - Models (Entity, PiccoloApp, migrations)
    - UI/API (Controller, Routes)
    - Events and Listeners
    - Errors and Providers
    
    \b
    Examples:
        porto make:module Blog
        porto make:module Product --section=ShopSection
        porto make:module Order --with-graphql --with-websocket
        porto make:module Payment --all
    """
    # Normalize name to PascalCase
    name = to_pascal_case(name)
    
    # If --all flag, enable all features
    if with_all:
        with_graphql = True
        with_websocket = True
        with_cli = True
        with_workers = True
    
    # Display generation info
    console.print(Panel.fit(
        f"[bold cyan]Porto Module Generator[/bold cyan]\n\n"
        f"[white]Module:[/white] [green]{name}Module[/green]\n"
        f"[white]Section:[/white] [green]{section}[/green]\n"
        f"[white]Path:[/white] [dim]src/Containers/{section}/{name}Module/[/dim]",
        title="[bold]Generating Module[/bold]",
        border_style="blue",
    ))
    
    # Show features table
    features = Table(show_header=True, header_style="bold")
    features.add_column("Feature", style="cyan")
    features.add_column("Status")
    
    features.add_row("GraphQL", "[green]Yes[/green]" if with_graphql else "[dim]No[/dim]")
    features.add_row("WebSocket", "[green]Yes[/green]" if with_websocket else "[dim]No[/dim]")
    features.add_row("CLI Commands", "[green]Yes[/green]" if with_cli else "[dim]No[/dim]")
    features.add_row("Background Workers", "[green]Yes[/green]" if with_workers else "[dim]No[/dim]")
    
    console.print(features)
    console.print()
    
    # Generate module
    try:
        generated = generate_module(
            name=name,
            section=section,
            with_graphql=with_graphql,
            with_websocket=with_websocket,
            with_cli=with_cli,
            with_workers=with_workers,
        )
        
        if generated:
            console.print(f"\n[bold green]Success![/bold green] Generated {len(generated)} files.")
            _print_next_steps(name, section)
        else:
            console.print("\n[yellow]No files were generated.[/yellow]")
            console.print("[dim]Module may already exist or templates are missing.[/dim]")
            
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        raise SystemExit(1)


def _print_next_steps(name: str, section: str) -> None:
    """Print next steps after module generation."""
    module_path = f"src/Containers/{section}/{name}Module"
    
    console.print(Panel.fit(
        f"[bold]Next steps:[/bold]\n\n"
        f"1. [cyan]Edit the model fields:[/cyan]\n"
        f"   {module_path}/Models/{name}.py\n\n"
        f"2. [cyan]Create database migration:[/cyan]\n"
        f"   litestar db makemigrations --app {name.lower()}\n\n"
        f"3. [cyan]Run migration:[/cyan]\n"
        f"   litestar db migrate\n\n"
        f"4. [cyan]Register the module:[/cyan]\n"
        f"   - Add provider to src/Ship/Providers/AppProvider.py\n"
        f"   - Add router to src/App.py\n\n"
        f"5. [cyan]Update Piccolo config:[/cyan]\n"
        f"   Add to piccolo_conf.py APPS list:\n"
        f"   'src.Containers.{section}.{name}Module.Models.PiccoloApp'",
        title="[bold green]What's Next?[/bold green]",
        border_style="green",
    ))

"""CLI command for generating Porto Queries.

Usage:
    porto make:query GetPost --module=Blog
    porto make:query ListProducts --module=Shop
"""

import click
from rich.console import Console
from rich.panel import Panel

from src.Ship.CLI.Generator import generate_component, to_pascal_case

console = Console()


@click.command("make:query")
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
def make_query(
    name: str,
    module: str,
    section: str,
    force: bool,
) -> None:
    """Generate a new Query (CQRS read operation) for a module.
    
    Queries are read-only operations for fetching data.
    They bypass UnitOfWork for better performance.
    
    \b
    CQRS Pattern:
    - Queries: Read operations (Get, List, Search, Find)
    - Actions: Write operations (Create, Update, Delete)
    
    \b
    Naming convention:
    - Get{Entity}Query: Single entity by ID
    - List{Entities}Query: Multiple entities with pagination
    - Search{Entities}Query: Search with filters
    - "Query" suffix is added automatically
    
    \b
    Examples:
        porto make:query GetPost --module=Blog
        porto make:query ListProducts --module=Shop
        porto make:query SearchUsers --module=User
    """
    # Normalize names
    name = to_pascal_case(name)
    module = to_pascal_case(module)
    
    # Remove "Query" suffix if provided
    if name.endswith("Query"):
        name = name[:-5]
    
    console.print(Panel.fit(
        f"[bold cyan]Query Generator[/bold cyan]\n\n"
        f"[white]Query:[/white] [green]{name}Query[/green]\n"
        f"[white]Module:[/white] [green]{module}Module[/green]\n"
        f"[white]Section:[/white] [green]{section}[/green]",
        title="[bold]Generating Query[/bold]",
        border_style="blue",
    ))
    
    try:
        generated = generate_component(
            component_type="query",
            component_name=name,
            module_name=module,
            section=section,
        )
        
        if generated:
            console.print(f"\n[bold green]Success![/bold green] Query created.")
            _print_next_steps(name, module, section)
        else:
            console.print("\n[yellow]Query was not created.[/yellow]")
            if not force:
                console.print("[dim]File may already exist. Use --force to overwrite.[/dim]")
                
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        raise SystemExit(1)


def _print_next_steps(name: str, module: str, section: str) -> None:
    """Print next steps after query generation."""
    query_path = f"src/Containers/{section}/{module}Module/Queries/{name}Query.py"
    
    console.print(Panel.fit(
        f"[bold]Next steps:[/bold]\n\n"
        f"1. [cyan]Implement the query logic:[/cyan]\n"
        f"   {query_path}\n\n"
        f"2. [cyan]Register in Providers.py (REQUEST scope):[/cyan]\n"
        f"   {name.lower()}_query = provide({name}Query)\n\n"
        f"3. [cyan]Usage in Controller:[/cyan]\n"
        f"   @get('/')\n"
        f"   async def list(self, query: FromDishka[{name}Query]) -> Response:\n"
        f"       result = await query.execute(input)\n"
        f"       return Response(result)",
        title="[bold green]What's Next?[/bold green]",
        border_style="green",
    ))

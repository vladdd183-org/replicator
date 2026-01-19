"""CLI command for generating Porto Events and Listeners.

Usage:
    porto make:event PostPublished --module=Blog
    porto make:event OrderCompleted --module=Order --with-listener
"""

import click
from rich.console import Console
from rich.panel import Panel

from src.Ship.CLI.Generator import to_pascal_case

console = Console()


@click.command("make:event")
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
    "--with-listener",
    is_flag=True,
    help="Also generate a listener for this event",
)
def make_event(
    name: str,
    module: str,
    section: str,
    with_listener: bool,
) -> None:
    """Generate a new Domain Event for a module.
    
    Domain Events represent something that happened in the domain.
    They are immutable and used for decoupling between modules.
    
    \b
    Event rules:
    - Named as past tense (e.g., UserCreated, OrderPlaced)
    - Immutable (frozen Pydantic model)
    - Contains only data needed by listeners
    - Published AFTER successful UnitOfWork commit
    
    \b
    Naming convention:
    - {Entity}{PastTenseVerb}: UserCreated, OrderPlaced, PaymentProcessed
    
    \b
    Examples:
        porto make:event PostPublished --module=Blog
        porto make:event OrderCompleted --module=Order --with-listener
        porto make:event PaymentProcessed --module=Payment
    """
    # Normalize names
    name = to_pascal_case(name)
    module = to_pascal_case(module)
    
    console.print(Panel.fit(
        f"[bold cyan]Event Generator[/bold cyan]\n\n"
        f"[white]Event:[/white] [green]{name}[/green]\n"
        f"[white]Module:[/white] [green]{module}Module[/green]\n"
        f"[white]Section:[/white] [green]{section}[/green]\n"
        f"[white]With Listener:[/white] {'[green]Yes[/green]' if with_listener else '[dim]No[/dim]'}",
        title="[bold]Generating Event[/bold]",
        border_style="blue",
    ))
    
    console.print("\n[yellow]Note:[/yellow] Events should be added manually to Events.py")
    console.print("[dim]This command generates a template you can copy into your Events.py file.[/dim]\n")
    
    _print_event_template(name, module, section)
    
    if with_listener:
        console.print()
        _print_listener_template(name, module, section)
    
    _print_next_steps(name, module, section, with_listener)


def _print_event_template(name: str, module: str, section: str) -> None:
    """Print event code template."""
    console.print(Panel.fit(
        f"[cyan]# Add to {module}Module/Events.py[/cyan]\n\n"
        f"class {name}(DomainEvent):\n"
        f'    """Event raised when {name.lower().replace("_", " ")}.\n'
        f"    \n"
        f"    Attributes:\n"
        f"        {module.lower()}_id: UUID of the {module.lower()}\n"
        f'    """\n'
        f"    \n"
        f"    {module.lower()}_id: UUID\n"
        f"    # Add more fields as needed",
        title="[bold]Event Template[/bold]",
        border_style="cyan",
    ))


def _print_listener_template(name: str, module: str, section: str) -> None:
    """Print listener code template."""
    console.print(Panel.fit(
        f"[cyan]# Add to {module}Module/Listeners.py[/cyan]\n\n"
        f'@listener("{name}")\n'
        f"async def on_{name.lower()}(\n"
        f"    {module.lower()}_id: str,\n"
        f"    app: Litestar | None = None,\n"
        f"    occurred_at: str | None = None,\n"
        f"    **kwargs,\n"
        f") -> None:\n"
        f'    """Handle {name} event.\n'
        f"    \n"
        f"    Triggered after {name.lower().replace('_', ' ')}.\n"
        f'    """\n'
        f"    logfire.info(\n"
        f'        "{name} event received",\n'
        f"        {module.lower()}_id={module.lower()}_id,\n"
        f"    )\n"
        f"    \n"
        f"    # TODO: Implement event handling logic",
        title="[bold]Listener Template[/bold]",
        border_style="cyan",
    ))


def _print_next_steps(name: str, module: str, section: str, with_listener: bool) -> None:
    """Print next steps after event generation."""
    console.print(Panel.fit(
        f"[bold]Next steps:[/bold]\n\n"
        f"1. [cyan]Add event to Events.py:[/cyan]\n"
        f"   src/Containers/{section}/{module}Module/Events.py\n\n"
        f"2. [cyan]Publish event in Action:[/cyan]\n"
        f"   self.uow.add_event({name}(\n"
        f"       {module.lower()}_id=entity.id,\n"
        f"   ))\n\n"
        + (
            f"3. [cyan]Add listener to Listeners.py:[/cyan]\n"
            f"   src/Containers/{section}/{module}Module/Listeners.py\n\n"
            f"4. [cyan]Register listener in App.py:[/cyan]\n"
            f"   from src.Containers.{section}.{module}Module.Listeners import on_{name.lower()}\n"
            f"   listeners=[on_{name.lower()}]"
            if with_listener else
            f"3. [cyan]Create listener (optional):[/cyan]\n"
            f"   porto make:event {name} --module={module} --with-listener"
        ),
        title="[bold green]What's Next?[/bold green]",
        border_style="green",
    ))

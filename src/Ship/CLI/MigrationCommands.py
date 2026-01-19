"""Database migration CLI commands.

Provides convenient wrappers around Piccolo migrations for Litestar CLI.
"""

import os
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console

console = Console()


def get_piccolo_path() -> str:
    """Get path to piccolo CLI executable in the same venv."""
    # Use the same Python as the running script
    venv_bin = Path(sys.executable).parent
    piccolo_path = venv_bin / "piccolo"
    
    if piccolo_path.exists():
        return str(piccolo_path)
    
    # Fallback: try to find in PATH
    return "piccolo"


def run_piccolo(*args: str) -> int:
    """Run piccolo CLI command."""
    piccolo = get_piccolo_path()
    result = subprocess.run(
        [piccolo] + list(args),
        capture_output=False,
    )
    return result.returncode


@click.group(name="db")
def db_group() -> None:
    """Database management commands.
    
    Available via Litestar CLI: litestar db <command>
    """
    pass


@db_group.command(name="migrate")
@click.option("--app-name", "-a", "app_name", default="all", help="App name or 'all' for all apps")
def migrate(app_name: str) -> None:
    """Run pending migrations (forwards).
    
    Example:
        litestar db migrate
        litestar db migrate --app-name user
    """
    console.print(f"\n[bold blue]🚀 Running migrations for: {app_name}[/bold blue]\n")
    
    returncode = run_piccolo("migrations", "forwards", app_name)
    
    if returncode == 0:
        console.print("\n[bold green]✓ Migrations completed successfully![/bold green]")
    else:
        console.print("\n[bold red]✗ Migration failed![/bold red]")
        sys.exit(1)


@db_group.command(name="makemigrations")
@click.option("--app-name", "-a", "app_name", default="all", help="App name or 'all' for all apps")
@click.option("--desc", "-d", default="", help="Migration description")
@click.option("--auto/--no-auto", default=True, help="Auto-detect changes")
def makemigrations(app_name: str, desc: str, auto: bool) -> None:
    """Create new migration based on model changes (auto).
    
    Example:
        litestar db makemigrations
        litestar db makemigrations --app-name user --desc "add phone field"
    """
    console.print(f"\n[bold blue]🔄 Creating migration for: {app_name}[/bold blue]\n")
    
    args = ["migrations", "new", app_name]
    
    if auto:
        args.append("--auto")
    
    if desc:
        args.extend(["--desc", desc])
    
    returncode = run_piccolo(*args)
    
    if returncode == 0:
        console.print("\n[bold green]✓ Migration created successfully![/bold green]")
    else:
        console.print("\n[bold red]✗ Failed to create migration![/bold red]")
        sys.exit(1)


@db_group.command(name="status")
@click.option("--app-name", "-a", "app_name", default="all", help="App name or 'all' for all apps")
def status(app_name: str) -> None:
    """Show migration status (which have run and which haven't).
    
    Example:
        litestar db status
        litestar db status --app-name user
    """
    console.print(f"\n[bold blue]📋 Migration status for: {app_name}[/bold blue]\n")
    
    run_piccolo("migrations", "check", app_name)


@db_group.command(name="rollback")
@click.option("--app-name", "-a", "app_name", required=True, help="App name")
@click.option("--migration", "-m", required=True, help="Migration ID to rollback to")
@click.confirmation_option(prompt="Are you sure you want to rollback migrations?")
def rollback(app_name: str, migration: str) -> None:
    """Rollback migrations to a specific point.
    
    Example:
        litestar db rollback --app-name user --migration 2024_01_01
    """
    console.print(f"\n[bold yellow]⚠️ Rolling back {app_name} to: {migration}[/bold yellow]\n")
    
    returncode = run_piccolo("migrations", "backwards", app_name, migration)
    
    if returncode == 0:
        console.print("\n[bold green]✓ Rollback completed![/bold green]")
    else:
        console.print("\n[bold red]✗ Rollback failed![/bold red]")
        sys.exit(1)


@db_group.command(name="reset")
@click.confirmation_option(prompt="⚠️ This will DELETE ALL DATA! Are you sure?")
def reset() -> None:
    """Reset database (drop all tables and re-run migrations).
    
    WARNING: This will delete all data!
    
    Example:
        litestar db reset
    """
    from src.Ship.Configs import get_settings
    
    settings = get_settings()
    db_path = settings.db_url.replace("sqlite:///", "")
    
    console.print("\n[bold red]🗑️ Resetting database...[/bold red]\n")
    
    # Remove SQLite database file
    if os.path.exists(db_path):
        os.remove(db_path)
        console.print(f"[dim]Removed: {db_path}[/dim]")
    
    # Run migrations
    returncode = run_piccolo("migrations", "forwards", "all")
    
    if returncode == 0:
        console.print("\n[bold green]✓ Database reset complete![/bold green]")
    else:
        console.print("\n[bold red]✗ Failed to reset database![/bold red]")
        sys.exit(1)


@db_group.command(name="shell")
def shell() -> None:
    """Open database SQL shell.
    
    Example:
        litestar db shell
    """
    console.print("\n[bold blue]🔧 Opening SQL shell...[/bold blue]\n")
    
    run_piccolo("sql_shell", "run")

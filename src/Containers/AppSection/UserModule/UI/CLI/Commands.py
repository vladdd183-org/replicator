"""CLI commands for UserModule.

Integrated with Litestar CLIPlugin via entry points.
Uses @with_container decorator for async DI container management.

NOTE: For new projects, consider using dishka.integrations.click directly:
    from dishka.integrations.click import setup_dishka, FromDishka, inject
    
    @click.command()
    @inject
    async def create_user(
        email: str,
        action: FromDishka[CreateUserAction],  # Auto-injected!
    ) -> None:
        ...

Usage:
    litestar users create --email user@example.com --password secret123 --name "John"
    litestar users get <user_id>
    litestar users list --limit 10
    litestar users delete <user_id> --force
"""

import click
from uuid import UUID
from rich.console import Console
from rich.table import Table
from returns.result import Success, Failure

from src.Ship.CLI.Decorators import with_container
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Actions.DeleteUserAction import DeleteUserAction
from src.Containers.AppSection.UserModule.Queries.ListUsersQuery import (
    ListUsersQuery,
    ListUsersQueryInput,
)
from src.Containers.AppSection.UserModule.Queries.GetUserQuery import (
    GetUserQuery,
    GetUserQueryInput,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import CreateUserRequest

console = Console()


@click.group(name="users")
def users_group() -> None:
    """User management commands.
    
    Available via Litestar CLI: litestar users <command>
    """
    pass


@users_group.command(name="create")
@click.option("--email", "-e", required=True, help="User email address")
@click.option("--password", "-p", required=True, help="User password (min 8 chars)")
@click.option("--name", "-n", required=True, help="User display name")
@with_container
async def create_user(container, email: str, password: str, name: str) -> None:
    """Create a new user.
    
    Example:
        litestar users create -e user@example.com -p password123 -n "John Doe"
    """
    action = await container.get(CreateUserAction)
    request = CreateUserRequest(email=email, password=password, name=name)
    result = await action.run(request)
    
    match result:
        case Success(user):
            console.print(f"[green]✓[/green] User created successfully!")
            console.print(f"  ID: {user.id}")
            console.print(f"  Email: {user.email}")
            console.print(f"  Name: {user.name}")
        case Failure(error):
            console.print(f"[red]✗[/red] Error: {error.message}")
            raise SystemExit(1)


@users_group.command(name="get")
@click.argument("user_id", type=click.UUID)
@with_container
async def get_user(container, user_id: UUID) -> None:
    """Get user by ID.
    
    Example:
        litestar users get 550e8400-e29b-41d4-a716-446655440000
    """
    query = await container.get(GetUserQuery)
    user = await query.execute(GetUserQueryInput(user_id=user_id))

    if user is None:
        console.print(f"[red]✗[/red] User not found")
        raise SystemExit(1)

    console.print(f"[bold]User Details[/bold]")
    console.print(f"  ID: {user.id}")
    console.print(f"  Email: {user.email}")
    console.print(f"  Name: {user.name}")
    console.print(f"  Active: {'Yes' if user.is_active else 'No'}")
    console.print(f"  Created: {user.created_at}")


@users_group.command(name="list")
@click.option("--limit", "-l", default=20, help="Maximum number of users")
@click.option("--offset", "-o", default=0, help="Number of users to skip")
@click.option("--active-only", "-a", is_flag=True, help="Show only active users")
@with_container
async def list_users(container, limit: int, offset: int, active_only: bool) -> None:
    """List all users with pagination.
    
    Uses CQRS Query directly for read operations.
    
    Example:
        litestar users list --limit 10 --active-only
    """
    query = await container.get(ListUsersQuery)
    output = await query.execute(
        ListUsersQueryInput(limit=limit, offset=offset, active_only=active_only)
    )

    table = Table(title="Users")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Email")
    table.add_column("Name")
    table.add_column("Active", justify="center")
    table.add_column("Created")

    for user in output.users:
        table.add_row(
            str(user.id)[:8] + "...",
            user.email,
            user.name,
            "✓" if user.is_active else "✗",
            str(user.created_at)[:19],
        )

    console.print(table)
    console.print(f"\nTotal: {output.total} | Showing: {len(output.users)}")


@users_group.command(name="delete")
@click.argument("user_id", type=click.UUID)
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@with_container
async def delete_user(container, user_id: UUID, force: bool) -> None:
    """Delete a user by ID (soft delete).
    
    Example:
        litestar users delete 550e8400-e29b-41d4-a716-446655440000 --force
    """
    if not force:
        if not click.confirm(f"Are you sure you want to delete user {user_id}?"):
            console.print("Cancelled.")
            return

    action = await container.get(DeleteUserAction)
    result = await action.run(user_id)

    match result:
        case Success(_):
            console.print(f"[green]✓[/green] User {user_id} deleted successfully!")
        case Failure(error):
            console.print(f"[red]✗[/red] Error: {error.message}")
            raise SystemExit(1)

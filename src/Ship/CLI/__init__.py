"""Ship CLI module.

CLI utilities and decorators for reduced boilerplate.

Usage with Dishka DI (recommended):
    from dishka.integrations.click import FromDishka, inject
    
    @click.command()
    @inject
    async def my_command(action: FromDishka[MyAction]) -> None:
        result = await action.run(...)
        handle_cli_result(result, success_message="Done!")

Legacy usage (deprecated):
    @click.command()
    @with_container
    async def my_command(container, ...):
        action = await container.get(MyAction)
        ...
"""

from src.Ship.CLI.Decorators import (
    with_container,
    handle_cli_result,
    get_cli_container,
    setup_cli_container,
)

__all__ = [
    "with_container",
    "handle_cli_result",
    "get_cli_container",
    "setup_cli_container",
]


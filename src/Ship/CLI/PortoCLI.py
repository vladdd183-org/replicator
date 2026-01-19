"""Porto Generator CLI - Standalone code generator.

This module provides a standalone CLI for code generation that doesn't require
Dishka DI container initialization. Use this for generating modules and components.

Usage:
    porto --help
    porto make:module Blog
    porto make:action CreatePost --module=Blog
    porto make:task SendEmail --module=Notification
    porto make:query GetPost --module=Blog
    porto make:controller Admin --module=User
    porto make:event PostPublished --module=Blog
"""

import click

# Import generator commands
from src.Ship.CLI.Commands import (
    make_module,
    make_action,
    make_task,
    make_query,
    make_controller,
    make_event,
)


@click.group()
@click.version_option(version="1.0.0", prog_name="Porto Generator")
def porto() -> None:
    """Hyper-Porto Code Generator.
    
    Generate modules, actions, tasks, queries, controllers, and events
    following Hyper-Porto architecture patterns.
    
    \b
    Available commands:
      make:module      Generate complete Porto module
      make:action      Generate Action (use case)
      make:task        Generate Task (atomic operation)
      make:query       Generate Query (CQRS read)
      make:controller  Generate HTTP Controller
      make:event       Generate Domain Event
    
    \b
    Examples:
        porto make:module Blog
        porto make:module Order --with-graphql --with-websocket
        porto make:action CreatePost --module=Blog
        porto make:task SendEmail --module=Notification --sync
    """
    pass


# Register generator commands
porto.add_command(make_module)
porto.add_command(make_action)
porto.add_command(make_task)
porto.add_command(make_query)
porto.add_command(make_controller)
porto.add_command(make_event)


if __name__ == "__main__":
    porto()

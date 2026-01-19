"""CLI commands for code generation and infrastructure.

Porto Generator Commands:
- make:module - Generate complete Porto module
- make:action - Generate Action (use case)
- make:task - Generate Task (atomic operation)
- make:query - Generate Query (CQRS read)
- make:controller - Generate HTTP Controller
- make:event - Generate Domain Event

Infrastructure Commands:
- temporal worker - Run Temporal worker
- temporal health - Check Temporal health
- temporal info - Show Temporal config
"""

from src.Ship.CLI.Commands.MakeModule import make_module
from src.Ship.CLI.Commands.MakeAction import make_action
from src.Ship.CLI.Commands.MakeTask import make_task
from src.Ship.CLI.Commands.MakeQuery import make_query
from src.Ship.CLI.Commands.MakeController import make_controller
from src.Ship.CLI.Commands.MakeEvent import make_event
from src.Ship.CLI.Commands.TemporalCommands import temporal_group

__all__ = [
    # Code generation
    "make_module",
    "make_action",
    "make_task",
    "make_query",
    "make_controller",
    "make_event",
    # Infrastructure
    "temporal_group",
]

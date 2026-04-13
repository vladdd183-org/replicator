from __future__ import annotations

from dishka import Provider, Scope, provide

from src.Containers.ToolSection.BeadsModule.Actions.CreateBeadAction import CreateBeadAction
from src.Containers.ToolSection.BeadsModule.Actions.ClaimBeadAction import ClaimBeadAction
from src.Containers.ToolSection.BeadsModule.Actions.CloseBeadAction import CloseBeadAction
from src.Containers.ToolSection.BeadsModule.Actions.ListReadyBeadsAction import ListReadyBeadsAction
from src.Containers.ToolSection.BeadsModule.Actions.AddDependencyAction import AddDependencyAction


class BeadsModuleProvider(Provider):
    scope = Scope.REQUEST
    create_bead = provide(CreateBeadAction)
    claim_bead = provide(ClaimBeadAction)
    close_bead = provide(CloseBeadAction)
    list_ready = provide(ListReadyBeadsAction)
    add_dep = provide(AddDependencyAction)

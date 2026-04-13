from __future__ import annotations

from dishka import Provider, Scope, provide

from src.Containers.ToolSection.GitModule.Actions.CloneRepoAction import (
    CloneRepoAction,
)
from src.Containers.ToolSection.GitModule.Actions.CommitChangesAction import (
    CommitChangesAction,
)
from src.Containers.ToolSection.GitModule.Actions.CreateBranchAction import (
    CreateBranchAction,
)


class GitModuleProvider(Provider):
    scope = Scope.REQUEST

    clone_repo = provide(CloneRepoAction)
    create_branch = provide(CreateBranchAction)
    commit_changes = provide(CommitChangesAction)

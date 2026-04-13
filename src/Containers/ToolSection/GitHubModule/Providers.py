from __future__ import annotations

from dishka import Provider, Scope, provide

from src.Containers.ToolSection.GitHubModule.Actions.CreatePRAction import CreatePRAction
from src.Containers.ToolSection.GitHubModule.Actions.EnableAutoMergeAction import EnableAutoMergeAction


class GitHubModuleProvider(Provider):
    scope = Scope.REQUEST
    create_pr = provide(CreatePRAction)
    auto_merge = provide(EnableAutoMergeAction)

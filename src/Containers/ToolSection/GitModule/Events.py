from __future__ import annotations

from src.Ship.Parents.Event import DomainEvent


class RepoCloned(DomainEvent):
    url: str
    local_path: str


class BranchCreated(DomainEvent):
    repo_path: str
    branch_name: str
    base_branch: str


class ChangesCommitted(DomainEvent):
    repo_path: str
    commit_hash: str
    message: str


class PRCreated(DomainEvent):
    repo_path: str
    pr_url: str
    title: str

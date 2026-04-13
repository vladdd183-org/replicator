from __future__ import annotations

from src.Ship.Core.Errors import BaseError


class GitError(BaseError):
    code: str = "GIT_ERROR"


class GitCloneError(GitError):
    code: str = "GIT_CLONE_ERROR"
    url: str = ""


class GitConflictError(GitError):
    code: str = "GIT_CONFLICT"
    http_status: int = 409
    branch: str = ""


class GitPushError(GitError):
    code: str = "GIT_PUSH_ERROR"
    remote: str = "origin"

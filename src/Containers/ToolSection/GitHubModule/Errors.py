from __future__ import annotations

from src.Ship.Core.Errors import BaseError


class GitHubError(BaseError):
    code: str = "GITHUB_ERROR"


class PRCreateError(GitHubError):
    code: str = "PR_CREATE_ERROR"


class PRMergeError(GitHubError):
    code: str = "PR_MERGE_ERROR"

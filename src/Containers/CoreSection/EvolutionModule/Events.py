from __future__ import annotations

from src.Ship.Parents.Event import DomainEvent


class VerificationPassed(DomainEvent):
    mission_id: str
    checks_passed: int
    evidence_summary: str = ""


class VerificationFailed(DomainEvent):
    mission_id: str
    checks_failed: int
    failure_reason: str = ""


class VersionPromoted(DomainEvent):
    mission_id: str
    commit_hash: str = ""
    promotion_type: str = ""

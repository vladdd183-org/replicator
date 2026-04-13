from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field

from src.Ship.Core.Types import BeadType, Complexity, IntentType, Priority


class MissionSpec(BaseModel):
    model_config = {"frozen": True}

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    intent_type: IntentType
    target: str = "self"
    acceptance_criteria: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    priority: Priority = Priority.MEDIUM


class StrategyPhase(BaseModel):
    model_config = {"frozen": True}

    name: str
    description: str
    dependencies: list[str] = Field(default_factory=list)
    parallel: bool = False


class StrategyPlan(BaseModel):
    model_config = {"frozen": True}

    approach: str
    phases: list[StrategyPhase] = Field(default_factory=list)
    risk_mitigations: list[str] = Field(default_factory=list)
    rollback_plan: str = ""
    estimated_beads: int = 0
    confidence: float = 0.0


class Bead(BaseModel):
    model_config = {"frozen": True}

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    bead_type: BeadType = BeadType.CODE
    acceptance_criteria: list[str] = Field(default_factory=list)
    input_artifacts: list[str] = Field(default_factory=list)
    output_artifacts: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    tools_required: list[str] = Field(default_factory=list)
    estimated_complexity: Complexity = Complexity.SIMPLE


class BeadGraph(BaseModel):
    model_config = {"frozen": True}

    beads: list[Bead] = Field(default_factory=list)
    edges: list[tuple[str, str]] = Field(default_factory=list)
    critical_path: list[str] = Field(default_factory=list)
    parallel_groups: list[list[str]] = Field(default_factory=list)


class BeadResult(BaseModel):
    model_config = {"frozen": True}

    bead_id: str
    status: str = "success"
    artifacts: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    duration_ms: int = 0
    agent_id: str = ""
    error_message: str = ""


class ExecutionResult(BaseModel):
    model_config = {"frozen": True}

    bead_results: list[BeadResult] = Field(default_factory=list)
    overall_status: str = "success"
    total_duration_ms: int = 0
    artifacts_produced: list[str] = Field(default_factory=list)


class EvidenceBundle(BaseModel):
    model_config = {"frozen": True}

    status: str = "pass"
    test_results: dict[str, Any] = Field(default_factory=dict)
    lint_results: dict[str, Any] = Field(default_factory=dict)
    type_check_results: dict[str, Any] = Field(default_factory=dict)
    diff_summary: str = ""
    metrics: dict[str, Any] = Field(default_factory=dict)
    risk_assessment: str = ""
    reviewer_notes: list[str] = Field(default_factory=list)

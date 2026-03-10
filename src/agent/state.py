"""State schema for the SUS Research Agent.

Defines the core data structures shared across all agent components:
execution trace entries, findings, reflections, and investigation state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class FindingConfidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CriticDecision(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    DEEPEN = "deepen"


# ---------------------------------------------------------------------------
# Execution trace
# ---------------------------------------------------------------------------


@dataclass
class CodeExecution:
    """Record of a single REPL execution."""

    node: str
    code: str
    output: str
    error: str | None = None
    artifacts: list[str] = field(default_factory=list)
    duration_ms: int = 0


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    """An established fact from the investigation."""

    id: str
    statement: str
    evidence: str
    so_what: str
    confidence: FindingConfidence = FindingConfidence.MEDIUM
    source_node: str = ""
    metrics: dict = field(default_factory=dict)


@dataclass
class Contradiction:
    """A finding that conflicts with a previously established fact."""

    new_finding_id: str
    existing_finding_id: str
    description: str


# ---------------------------------------------------------------------------
# Critic output
# ---------------------------------------------------------------------------


@dataclass
class CriticVerdict:
    """Result of a single critic test."""

    test_name: str
    passed: bool
    reasoning: str


@dataclass
class Reflection:
    """Output from the Critic after evaluating an analysis step."""

    phase: str
    verdicts: list[CriticVerdict]
    decision: CriticDecision
    summary: str
    suggestions: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.decision == CriticDecision.PASS

    @property
    def failed_tests(self) -> list[CriticVerdict]:
        return [v for v in self.verdicts if not v.passed]


# ---------------------------------------------------------------------------
# Hypothesis (for future sprints, kept minimal)
# ---------------------------------------------------------------------------


@dataclass
class Hypothesis:
    id: str
    statement: str
    test_method: str
    status: Literal["pending", "confirmed", "rejected", "inconclusive"] = "pending"


# ---------------------------------------------------------------------------
# Investigation state
# ---------------------------------------------------------------------------


@dataclass
class InvestigationState:
    """Top-level state for an investigation run."""

    # Input
    research_question: str = ""
    icd10_prefix: str = ""
    uf: str = "SP"
    year_range: tuple[int, int] = (2016, 2025)

    # Data paths
    data_dir: str = ""
    output_dir: str = ""

    # Execution trace
    trace: list[CodeExecution] = field(default_factory=list)

    # Findings
    findings: list[Finding] = field(default_factory=list)
    contradictions: list[Contradiction] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)

    # Reflections
    reflections: list[Reflection] = field(default_factory=list)

    # Control
    current_step: str = ""
    errors: list[str] = field(default_factory=list)

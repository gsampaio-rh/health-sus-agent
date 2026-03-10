"""Tests for agent state schema."""

from src.agent.state import (
    CodeExecution,
    CriticDecision,
    CriticVerdict,
    Finding,
    FindingConfidence,
    InvestigationState,
    Reflection,
)


def test_code_execution_defaults():
    entry = CodeExecution(node="eda", code="print(1)", output="1\n")
    assert entry.error is None
    assert entry.artifacts == []
    assert entry.duration_ms == 0


def test_finding_with_metrics():
    finding = Finding(
        id="f1",
        statement="Mortality is 33%",
        evidence="df['MORTE'].mean() = 0.33",
        so_what="Interventions needed",
        confidence=FindingConfidence.HIGH,
        metrics={"mortality_rate": 0.33},
    )
    assert finding.confidence == FindingConfidence.HIGH
    assert finding.metrics["mortality_rate"] == 0.33


def test_reflection_passed_property():
    reflection = Reflection(
        phase="eda",
        verdicts=[
            CriticVerdict(test_name="circularity", passed=True, reasoning="ok"),
            CriticVerdict(test_name="depth", passed=True, reasoning="ok"),
        ],
        decision=CriticDecision.PASS,
        summary="Good analysis",
    )
    assert reflection.passed is True
    assert reflection.failed_tests == []


def test_reflection_failed_tests():
    reflection = Reflection(
        phase="eda",
        verdicts=[
            CriticVerdict(test_name="circularity", passed=True, reasoning="ok"),
            CriticVerdict(test_name="depth", passed=False, reasoning="too shallow"),
        ],
        decision=CriticDecision.DEEPEN,
        summary="Needs more depth",
    )
    assert reflection.passed is False
    assert len(reflection.failed_tests) == 1
    assert reflection.failed_tests[0].test_name == "depth"


def test_investigation_state_defaults():
    state = InvestigationState()
    assert state.uf == "SP"
    assert state.year_range == (2016, 2025)
    assert state.trace == []
    assert state.findings == []
    assert state.errors == []

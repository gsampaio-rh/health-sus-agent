"""Tests for the Findings Accumulator."""

from src.agent.accumulator import FindingsAccumulator
from src.agent.state import Finding, FindingConfidence


def _make_finding(id: str, statement: str, **kwargs) -> Finding:
    defaults = {
        "evidence": "test evidence",
        "so_what": "test implication",
        "confidence": FindingConfidence.MEDIUM,
    }
    defaults.update(kwargs)
    return Finding(id=id, statement=statement, **defaults)


def test_add_finding():
    acc = FindingsAccumulator()
    f = _make_finding("f1", "Mortality is 33%")
    contradictions = acc.add_finding(f)
    assert len(acc.facts) == 1
    assert contradictions == []


def test_detect_contradiction():
    acc = FindingsAccumulator()
    f1 = _make_finding("f1", "Mortality is 33%", metrics={"mortality_rate": 0.33})
    f2 = _make_finding("f2", "Mortality is 45%", metrics={"mortality_rate": 0.45})
    acc.add_finding(f1)
    contradictions = acc.add_finding(f2)
    assert len(contradictions) == 1
    assert "f1" in contradictions[0].existing_finding_id
    assert "f2" in contradictions[0].new_finding_id


def test_no_contradiction_for_similar_values():
    acc = FindingsAccumulator()
    f1 = _make_finding("f1", "Rate A", metrics={"rate": 0.33})
    f2 = _make_finding("f2", "Rate B", metrics={"rate": 0.34})
    acc.add_finding(f1)
    contradictions = acc.add_finding(f2)
    assert contradictions == []


def test_open_questions():
    acc = FindingsAccumulator()
    acc.add_open_question("Why is mortality rising?")
    acc.add_open_question("Why is mortality rising?")  # duplicate
    assert len(acc.open_questions) == 1

    acc.resolve_question("Why is mortality rising?")
    assert len(acc.open_questions) == 0


def test_summary_empty():
    acc = FindingsAccumulator()
    assert acc.summary() == ""


def test_summary_with_findings():
    acc = FindingsAccumulator()
    acc.add_finding(_make_finding("f1", "Mortality is 33%", so_what="Interventions needed"))
    acc.add_open_question("What drives the trend?")
    summary = acc.summary()
    assert "Mortality is 33%" in summary
    assert "Interventions needed" in summary
    assert "What drives the trend?" in summary

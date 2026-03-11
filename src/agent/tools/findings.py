"""Finding management tools — record findings, check contradictions.

These wrap the FindingsAccumulator so the agent can interact with it
through structured tool calls.
"""

from __future__ import annotations

from src.agent.accumulator import FindingsAccumulator
from src.agent.state import Finding, FindingConfidence

_accumulator: FindingsAccumulator | None = None


def set_accumulator(acc: FindingsAccumulator) -> None:
    global _accumulator
    _accumulator = acc


def _get_accumulator() -> FindingsAccumulator:
    global _accumulator
    if _accumulator is None:
        _accumulator = FindingsAccumulator()
    return _accumulator


def _has_template_placeholders(text: str) -> bool:
    """Detect unfilled Python-style template placeholders like {variable}."""
    import re
    return bool(re.search(r"\{[a-zA-Z_]\w*(?::[^}]*)?\}", text))


def record_finding(
    finding_id: str,
    statement: str,
    evidence: str,
    so_what: str,
    confidence: str = "medium",
    source_step: str = "",
    metrics: dict | None = None,
) -> str:
    """Record a research finding.

    Args:
        finding_id: Unique identifier for the finding.
        statement: What was discovered (1-2 sentences).
        evidence: What data supports this (specific numbers).
        so_what: Why it matters / what action it implies.
        confidence: "low", "medium", or "high".
        source_step: Which analysis step produced this.
        metrics: Optional numeric metrics dict.

    Returns:
        Confirmation + any contradictions detected.
    """
    if _has_template_placeholders(statement):
        return (
            f"Error: statement contains unfilled placeholders: '{statement}'. "
            f"Use actual numbers from prior tool results, not template variables."
        )

    acc = _get_accumulator()

    conf_map = {
        "low": FindingConfidence.LOW,
        "medium": FindingConfidence.MEDIUM,
        "high": FindingConfidence.HIGH,
    }

    finding = Finding(
        id=finding_id,
        statement=statement,
        evidence=evidence,
        so_what=so_what,
        confidence=conf_map.get(confidence, FindingConfidence.MEDIUM),
        source_node=source_step,
        metrics=metrics or {},
    )

    contradictions = acc.add_finding(finding)

    result = f"Finding recorded: [{confidence}] {statement}"
    if contradictions:
        for c in contradictions:
            result += f"\n  CONTRADICTION: {c.description}"
    return result


def get_findings_summary() -> str:
    """Get a summary of all findings so far."""
    acc = _get_accumulator()
    summary = acc.summary()
    return summary or "No findings recorded yet."


def add_open_question(question: str) -> str:
    """Record an open question for future investigation."""
    acc = _get_accumulator()
    acc.add_open_question(question)
    return f"Open question added: {question}"

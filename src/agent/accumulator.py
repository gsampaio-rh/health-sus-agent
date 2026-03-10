"""Findings Accumulator — persistent cross-step knowledge store.

Maintains established facts, contradictions, and open questions across
analysis steps. Prevents linear thinking by making all prior knowledge
available to each new step and the Critic.
"""

from __future__ import annotations

from src.agent.state import Contradiction, Finding


class FindingsAccumulator:
    """Tracks facts, contradictions, and open questions across analysis steps."""

    def __init__(self) -> None:
        self.facts: list[Finding] = []
        self.contradictions: list[Contradiction] = []
        self.open_questions: list[str] = []

    def add_finding(self, finding: Finding) -> list[Contradiction]:
        """Add a finding and check for contradictions with existing facts.

        Returns any new contradictions detected.
        """
        new_contradictions: list[Contradiction] = []

        for existing in self.facts:
            if self._may_contradict(existing, finding):
                contradiction = Contradiction(
                    new_finding_id=finding.id,
                    existing_finding_id=existing.id,
                    description=(
                        f"New finding '{finding.statement}' may contradict "
                        f"existing finding '{existing.statement}'"
                    ),
                )
                new_contradictions.append(contradiction)

        self.facts.append(finding)
        self.contradictions.extend(new_contradictions)
        return new_contradictions

    def add_open_question(self, question: str) -> None:
        if question not in self.open_questions:
            self.open_questions.append(question)

    def resolve_question(self, question: str) -> None:
        if question in self.open_questions:
            self.open_questions.remove(question)

    def summary(self) -> str:
        """Produce a text summary for the Critic's context window."""
        if not self.facts and not self.open_questions:
            return ""

        parts: list[str] = []

        if self.facts:
            parts.append("### Established findings")
            for f in self.facts:
                confidence_tag = f"[{f.confidence.value}]"
                parts.append(f"- {confidence_tag} {f.statement}")
                if f.so_what:
                    parts.append(f"  So what: {f.so_what}")

        if self.contradictions:
            parts.append("\n### Contradictions (need resolution)")
            for c in self.contradictions:
                parts.append(f"- {c.description}")

        if self.open_questions:
            parts.append("\n### Open questions")
            for q in self.open_questions:
                parts.append(f"- {q}")

        return "\n".join(parts)

    @staticmethod
    def _may_contradict(existing: Finding, new: Finding) -> bool:
        """Heuristic: two findings contradict if they share metrics keys
        with substantially different values.

        This is intentionally conservative — flags for human/Critic review
        rather than auto-resolving.
        """
        if not existing.metrics or not new.metrics:
            return False

        shared_keys = set(existing.metrics) & set(new.metrics)
        for key in shared_keys:
            old_val = existing.metrics[key]
            new_val = new.metrics[key]
            if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                if old_val == 0:
                    continue
                pct_change = abs(new_val - old_val) / abs(old_val)
                if pct_change > 0.20:
                    return True
        return False

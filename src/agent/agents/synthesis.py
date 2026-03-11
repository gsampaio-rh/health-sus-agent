"""SynthesisAgent — consolidates all findings into final reports.

Reads all RQ reports and produces:
  - reports/executive_summary.md
  - FINDINGS.md (top-level, for human readers)
"""

from __future__ import annotations

from src.agent.agents.base import BaseAgent


class SynthesisAgent(BaseAgent):

    @property
    def agent_name(self) -> str:
        return "synthesis"

    @property
    def skill_names(self) -> list[str]:
        return ["report_writing"]

    def system_prompt(self) -> str:
        return """\
You are a research synthesis agent. You consolidate multiple research \
reports into a coherent executive summary and findings document.

Your job is to:
1. Identify the most important findings across all reports
2. Connect findings into a coherent narrative
3. Highlight contradictions and open questions
4. Recommend policy actions based on evidence
5. Write for the target audience (typically policymakers)

Write in the specified language. Be specific — use numbers, not adjectives.
"""

    def build_user_prompt(self) -> str:
        return ""

    def run(self):
        """Override: no tool loop. Pure LLM synthesis from reports."""
        import time

        from loguru import logger

        from src.agent.agents.base import AgentResult

        start = time.perf_counter()
        logger.info(f"[{self.agent_name}] Synthesizing findings")

        self.scratchpad.goal = "Synthesize all findings into executive summary"

        all_reports = self._load_all_reports()
        findings_text = self.context.findings_summary()

        synthesis_prompt = f"""\
## Investigation
{self.context.question}

**ICD-10:** {self.context.icd10_prefix} | \
**Period:** {self.context.year_range[0]}-{self.context.year_range[1]}

## All Research Reports

{all_reports}

## Accumulated Findings

{findings_text}

## Open Questions

{chr(10).join(f"- {q}" for q in self.context.open_questions) or "None"}

## Task

Write TWO documents:

### Document 1: Executive Summary (executive_summary.md)

Structure:
1. The Headline — one paragraph summary
2. Key Findings (numbered, with specific numbers)
3. Access Gaps / Equity Issues
4. Contradictions and Limitations
5. Recommended Actions
6. Open Questions for Further Research
7. Methodology Summary

### Document 2: FINDINGS.md (brief, scannable)

Structure:
1. One-paragraph headline
2. Key metrics table
3. Root cause analysis
4. Policy recommendations (3-5 bullet points)

Separate the two documents with "---SPLIT---".
Write in {self.context.language}.
"""

        raw = self._ask_llm(self.system_prompt(), synthesis_prompt)

        if "---SPLIT---" in raw:
            parts = raw.split("---SPLIT---", 1)
            exec_summary = parts[0].strip()
            findings_doc = parts[1].strip()
        else:
            exec_summary = raw
            findings_doc = self._generate_findings_doc()

        # Clean markdown fences
        for doc in [exec_summary, findings_doc]:
            if doc.startswith("```"):
                doc = doc.split("\n", 1)[1] if "\n" in doc else doc
                if doc.endswith("```"):
                    doc = doc[:-3]

        exec_path = self._save_doc("reports/executive_summary.md", exec_summary)
        self._save_doc("FINDINGS.md", findings_doc)

        self._save_trace()

        duration = int((time.perf_counter() - start) * 1000)
        logger.info(f"[{self.agent_name}] Synthesis completed in {duration}ms")

        return AgentResult(
            agent_name=self.agent_name,
            report_path=exec_path,
            report_content=exec_summary,
            scratchpad=self.scratchpad,
            duration_ms=duration,
        )

    def _load_all_reports(self) -> str:
        reports_dir = self.run_dir / "reports"
        if not reports_dir.exists():
            return "No reports found."

        parts = []
        for md_file in sorted(reports_dir.glob("*.md")):
            if md_file.stem in ("executive_summary", "FINDINGS"):
                continue
            content = md_file.read_text(encoding="utf-8")
            parts.append(f"### {md_file.stem}\n\n{content}")

        return "\n\n---\n\n".join(parts) if parts else "No reports found."

    def _generate_findings_doc(self) -> str:
        """Fallback if LLM doesn't produce a split document."""
        lines = [
            f"# {self.context.icd10_prefix} Investigation — Findings",
            "",
            f"**Question:** {self.context.question}",
            "",
            "---",
            "",
        ]

        if self.context.findings:
            lines.append("## Key Findings")
            lines.append("")
            for f in self.context.findings:
                statement = f.get("statement", "")
                confidence = f.get("confidence", "medium")
                lines.append(f"- [{confidence}] {statement}")
            lines.append("")

        if self.context.open_questions:
            lines.append("## Open Questions")
            lines.append("")
            for q in self.context.open_questions:
                lines.append(f"- {q}")
            lines.append("")

        return "\n".join(lines)

    def _save_doc(self, rel_path: str, content: str) -> str:
        full_path = self.run_dir / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return str(full_path)

    def generate_report(self) -> str:
        return ""

    def _report_filename(self) -> str:
        return "executive_summary.md"

"""RQAgent — investigates a single research question.

Produces: reports/NN_rq_title.md

Uses the GPAOR loop with tool calls to analyze data,
then generates a structured markdown report.
"""

from __future__ import annotations

from src.agent.agents.base import BaseAgent, build_tools_description
from src.agent.context import ResearchQuestion


class RQAgent(BaseAgent):
    """Agent that investigates one research question."""

    def __init__(self, *args, rq: ResearchQuestion, rq_index: int = 0, **kwargs):
        self.rq = rq
        self.rq_index = rq_index
        self.prior_errors: str = ""
        super().__init__(*args, **kwargs)

    @property
    def agent_name(self) -> str:
        return f"rq_{self.rq.id}"

    @property
    def skill_names(self) -> list[str]:
        return ["sus_domain", "eda_patterns", "statistical_tests", "report_writing"]

    def system_prompt(self) -> str:
        skill_text = self.skill.compact if self.skill.raw_content else ""

        main_dataset = self._find_main_dataset()

        return f"""\
You are a research agent investigating a specific question about Brazilian \
SUS public health data. You use pre-built analysis tools to explore the data, \
then record your findings.

{skill_text}

## Available tools

{build_tools_description()}

## Instructions

Investigate the given research question by:
1. Start with aggregate or time_series to get overview data
2. Decompose findings along the specified dimension
3. Run statistical tests where appropriate
4. Create charts for key patterns
5. Record findings with record_finding (include specific numbers)
6. Add open questions for things you can't answer

IMPORTANT:
- The main dataset is "{main_dataset}" — use this name in tool calls
- ALL datasets are ALREADY loaded — do NOT call load_dataset
- To create charts, first use aggregate/time_series with new_name to save results, \
then use create_chart referencing that saved dataset name
- Record findings with record_finding (include specific numbers)
- Consider confounders before drawing conclusions

Respond ONLY with a JSON array of tool calls, using EXACTLY this format:
[{{"tool": "tool_name", "args": {{"param1": "value1"}}}}]

EVERY call must have both "tool" and "args" keys. Respond with [] when done. \
Do NOT include any text outside the JSON array.
"""

    def build_user_prompt(self) -> str:
        catalog_text = self.context.data_catalog.to_prompt()
        findings_so_far = self.context.findings_summary()

        prior_reports = self._load_prior_reports()

        error_context = ""
        if self.prior_errors:
            error_context = (
                "## RETRY — Previous errors to avoid\n\n"
                "A prior run of this agent failed on these calls. "
                "Use the correct dataset names and column names.\n\n"
                f"{self.prior_errors}\n\n"
            )

        return (
            f"## Research Question: {self.rq.title}\n\n"
            f"**ID:** {self.rq.id}\n"
            f"**Description:** {self.rq.description}\n"
            f"**Expected output:** {self.rq.output_type}\n"
            f"**Decomposition:** {self.rq.decomposition}\n\n"
            f"## Available Datasets (use ONLY these names and columns)\n\n"
            f"{catalog_text}\n\n"
            f"{error_context}"
            f"## Previously established findings\n{findings_so_far}\n\n"
            f"{prior_reports}"
            f"What tool calls should I make to investigate this question?"
        )

    def _find_main_dataset(self) -> str:
        schemas = self.context.data_catalog.schemas
        for s in schemas:
            if "sih" in s.name.lower():
                return s.name
        return schemas[0].name if schemas else "sih"

    def _load_prior_reports(self) -> str:
        """Load reports from completed RQs for context."""
        reports_dir = self.run_dir / "reports"
        if not reports_dir.exists():
            return ""

        parts = []
        for rq_id in self.context.completed_rqs:
            for md_file in sorted(reports_dir.glob("*.md")):
                if rq_id in md_file.stem:
                    content = md_file.read_text(encoding="utf-8")
                    parts.append(
                        f"## Prior report: {rq_id}\n\n"
                        f"{content[:1500]}\n\n---\n"
                    )
                    break

        if parts:
            return "## Context from prior analyses\n\n" + "\n".join(parts) + "\n\n"
        return ""

    def generate_report(self) -> str:
        """Generate the research report using LLM to synthesize tool results."""
        observations = "\n".join(
            f"- {obs}" for obs in self.scratchpad.observations[:30]
        )
        artifacts = "\n".join(
            f"- {a}" for a in self.trace.artifacts
        )

        report_prompt = f"""\
Generate a structured research report in markdown for this research question.

## Research Question
**{self.rq.title}**
{self.rq.description}

## Tool Results (observations from analysis)
{observations}

## Charts Produced
{artifacts or "None"}

## Report Format
Use this exact structure:

# Report {self.rq_index:02d} — {self.rq.title}

> **Research Question:** {self.rq.description}

---

## Method
[Describe the analytical approach used]

## Key Findings

### 1. [Finding Title]
[Narrative with specific numbers, tables, and chart references]

## Limitations
[What this analysis cannot answer]

## Implications
[Policy/action recommendations]

Write the report in {self.context.language}. Include specific numbers \
from the observations. Reference charts using ![](../plots/filename.png).
"""

        try:
            report = self._ask_llm(
                "You are a research report writer. Write clear, evidence-based "
                "reports with specific numbers and actionable insights.",
                report_prompt,
            )
            # Strip any markdown code fences the LLM might wrap it in
            if report.startswith("```"):
                report = report.split("\n", 1)[1] if "\n" in report else report
                if report.endswith("```"):
                    report = report[:-3]
            return report.strip()
        except Exception as e:
            return (
                f"# Report {self.rq_index:02d} — {self.rq.title}\n\n"
                f"> Report generation failed: {e}\n\n"
                f"## Raw Observations\n\n{observations}"
            )

    def _report_filename(self) -> str:
        return f"{self.rq_index:02d}_{self.rq.id}.md"

    def _get_goal(self) -> str:
        return f"Investigate: {self.rq.title} — {self.rq.description[:100]}"

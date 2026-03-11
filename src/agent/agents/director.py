"""DirectorAgent — creates the investigation plan.

Takes a research question and produces:
  - reports/00_plan.md
  - context.json (updated with plan details)
"""

from __future__ import annotations

import json

from src.agent.agents.base import BaseAgent
from src.agent.context import ResearchQuestion
from src.agent.critic import _extract_json


class DirectorAgent(BaseAgent):

    @property
    def agent_name(self) -> str:
        return "director"

    @property
    def skill_names(self) -> list[str]:
        return ["sus_domain", "eda_patterns"]

    def system_prompt(self) -> str:
        skill_text = self.skill.compact if self.skill.raw_content else ""
        return f"""\
You are a research director planning an investigation of Brazilian SUS \
public health data. You design structured investigations that answer \
specific research questions.

{skill_text}

Given a research question, produce a JSON investigation plan with:
1. The ICD-10 prefix to filter on
2. State (UF) and year range
3. Audience and language for reports
4. Domain priors — facts the audience already knows
5. 5-8 research questions, ordered from overview to deep analysis

Each research question should have:
- id: short snake_case identifier
- title: human-readable title
- description: what to investigate (2-3 sentences)
- output_type: "chart", "metric", "table", or "narrative"
- decomposition: which dimension to analyze by

Respond with ONLY valid JSON:
{{
  "icd10_prefix": "string",
  "uf": "string",
  "year_range": [int, int],
  "audience": "string",
  "language": "string",
  "domain_priors": ["string"],
  "research_questions": [
    {{
      "id": "string",
      "title": "string",
      "description": "string",
      "output_type": "string",
      "decomposition": "string",
      "depends_on": ["string"]
    }}
  ]
}}

Guidelines:
- Start with a general overview, then progressively deeper questions
- Always include age, geography, and time decompositions
- Always include a confounder-adjusted analysis
- End with policy implications
"""

    def build_user_prompt(self) -> str:
        return f"Research question: {self.context.question}"

    def run(self):
        """Override: DirectorAgent uses a single LLM call, no tool loop."""
        import time

        from loguru import logger

        from src.agent.agents.base import AgentResult

        start = time.perf_counter()
        logger.info(f"[{self.agent_name}] Planning investigation")

        self.scratchpad.goal = f"Create investigation plan for: {self.context.question}"

        raw = self._ask_llm(self.system_prompt(), self.build_user_prompt())

        try:
            text = _extract_json(raw)
            plan_data = json.loads(text)
        except (json.JSONDecodeError, ValueError) as e:
            duration = int((time.perf_counter() - start) * 1000)
            logger.error(f"[{self.agent_name}] Failed to parse plan: {e}")
            return AgentResult(
                agent_name=self.agent_name,
                error=f"Failed to parse plan JSON: {e}",
                duration_ms=duration,
            )

        self.context.icd10_prefix = plan_data.get("icd10_prefix", "")
        self.context.uf = plan_data.get("uf", "SP")
        yr = plan_data.get("year_range", [2016, 2025])
        self.context.year_range = (yr[0], yr[1])
        self.context.audience = plan_data.get("audience", "Brazilian health policymakers")
        self.context.language = plan_data.get("language", "pt-BR")
        self.context.domain_priors = plan_data.get("domain_priors", [])

        self.context.research_questions = [
            ResearchQuestion(
                id=rq.get("id", f"rq_{i}"),
                title=rq.get("title", ""),
                description=rq.get("description", ""),
                output_type=rq.get("output_type", "chart"),
                decomposition=rq.get("decomposition", ""),
                depends_on=rq.get("depends_on", []),
            )
            for i, rq in enumerate(plan_data.get("research_questions", []))
        ]

        self.scratchpad.plan = [
            f"{rq.id}: {rq.title}" for rq in self.context.research_questions
        ]

        report = self.generate_report()
        report_path = self._save_report(report)

        ctx_path = self.run_dir / "context.json"
        self.context.save(ctx_path)

        self._save_trace()

        duration = int((time.perf_counter() - start) * 1000)
        logger.info(
            f"[{self.agent_name}] Plan created in {duration}ms: "
            f"{self.context.icd10_prefix}, "
            f"{len(self.context.research_questions)} research questions"
        )

        return AgentResult(
            agent_name=self.agent_name,
            report_path=report_path,
            report_content=report,
            scratchpad=self.scratchpad,
            duration_ms=duration,
        )

    def generate_report(self) -> str:
        lines = [
            "# Investigation Plan",
            "",
            f"> **Research Question:** {self.context.question}",
            "",
            f"**ICD-10:** {self.context.icd10_prefix} | "
            f"**State:** {self.context.uf} | "
            f"**Period:** {self.context.year_range[0]}-{self.context.year_range[1]}",
            "",
            "---",
            "",
            "## Research Questions",
            "",
        ]

        for i, rq in enumerate(self.context.research_questions):
            deps = f" (depends on: {', '.join(rq.depends_on)})" if rq.depends_on else ""
            lines.append(f"### {i + 1}. {rq.title} (`{rq.id}`)")
            lines.append("")
            lines.append(rq.description)
            lines.append("")
            lines.append(
                f"**Output:** {rq.output_type} | "
                f"**Decomposition:** {rq.decomposition}{deps}"
            )
            lines.append("")

        if self.context.domain_priors:
            lines.append("## Domain Priors")
            lines.append("")
            for prior in self.context.domain_priors:
                lines.append(f"- {prior}")
            lines.append("")

        return "\n".join(lines)

    def _report_filename(self) -> str:
        return "00_plan.md"

"""Planner — LLM-driven investigation planning.

Takes a research question + skill context and produces an InvestigationPlan
with ICD-10 prefix, data sources, analysis steps, and domain priors.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.agent.critic import _extract_json
from src.agent.skill import SkillContext

PLANNER_SYSTEM_PROMPT = """\
You are a research planner for public health investigations using Brazilian \
SUS (Sistema Unico de Saude) data. Your job is to take a research question \
and produce a structured investigation plan.

You have deep domain knowledge about SUS data systems, provided below.

{skill_context}

Given a research question, produce a plan with:
1. The ICD-10 prefix to filter on (e.g., "J96" for respiratory failure)
2. The state (UF) and year range to analyze
3. The audience and language for the final report
4. A list of 5-8 analysis steps, ordered from EDA to deep analysis
5. Domain priors — things the audience already knows (for the Critic)
6. Data sources needed (parquet file patterns)

Each analysis step should have:
- A short name (e.g., "mortality_by_age")
- A description of what to analyze (NOT code — the code generator writes code)
- The expected output type (chart, metric, table, or narrative)
- Which dimension it decomposes by (time, age, geography, facility, procedure)

Respond with ONLY valid JSON matching this schema:
{{
  "icd10_prefix": "string",
  "uf": "string",
  "year_range": [int, int],
  "audience": "string",
  "language": "string",
  "data_sources": ["string"],
  "domain_priors": ["string"],
  "analysis_steps": [
    {{
      "name": "string",
      "description": "string",
      "output_type": "chart" | "metric" | "table" | "narrative",
      "decomposition": "string"
    }}
  ]
}}

Guidelines:
- Start with data loading and overview, then decompose progressively
- Always include age, geography, and time decompositions
- Always include a confounder-adjusted analysis
- Always end with a "so what" step that connects to policy
- Order steps so each builds on findings from previous steps
"""


@dataclass
class AnalysisStep:
    """A single step in the investigation plan."""

    name: str
    description: str
    output_type: str = "chart"
    decomposition: str = ""


@dataclass
class InvestigationPlan:
    """Complete investigation plan produced by the Planner."""

    question: str
    icd10_prefix: str
    uf: str = "SP"
    year_range: tuple[int, int] = (2016, 2025)
    audience: str = "Brazilian health policymakers"
    language: str = "pt-BR"
    data_sources: list[str] = field(default_factory=list)
    domain_priors: list[str] = field(default_factory=list)
    analysis_steps: list[AnalysisStep] = field(default_factory=list)


def _parse_plan(raw: str, question: str) -> InvestigationPlan:
    """Parse LLM JSON response into an InvestigationPlan."""
    text = _extract_json(raw)
    data = json.loads(text)

    steps = [
        AnalysisStep(
            name=s["name"],
            description=s["description"],
            output_type=s.get("output_type", "chart"),
            decomposition=s.get("decomposition", ""),
        )
        for s in data["analysis_steps"]
    ]

    year_range = data.get("year_range", [2016, 2025])

    return InvestigationPlan(
        question=question,
        icd10_prefix=data["icd10_prefix"],
        uf=data.get("uf", "SP"),
        year_range=(year_range[0], year_range[1]),
        audience=data.get("audience", "Brazilian health policymakers"),
        language=data.get("language", "pt-BR"),
        data_sources=data.get("data_sources", []),
        domain_priors=data.get("domain_priors", []),
        analysis_steps=steps,
    )


class Planner:
    """LLM-driven investigation planner."""

    def __init__(self, llm: BaseChatModel, skill: SkillContext | None = None):
        self.llm = llm
        self.skill = skill

    def create_plan(self, question: str) -> InvestigationPlan:
        """Generate an investigation plan from a research question."""
        skill_text = ""
        if self.skill and self.skill.raw_content:
            skill_text = (
                "## SUS Domain Knowledge\n\n" + self.skill.compact
            )

        system = PLANNER_SYSTEM_PROMPT.format(skill_context=skill_text)

        messages = [
            SystemMessage(content=system),
            HumanMessage(content=f"Research question: {question}"),
        ]

        response = self.llm.invoke(messages)
        return _parse_plan(response.content, question)

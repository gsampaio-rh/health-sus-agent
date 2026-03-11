"""Tests for the Planner."""

from unittest.mock import MagicMock

from src.agent.planner import (
    AnalysisStep,
    InvestigationPlan,
    Planner,
    _parse_plan,
)
from src.agent.skill import SkillContext

SAMPLE_PLAN_JSON = """\
{
  "icd10_prefix": "J96",
  "uf": "SP",
  "year_range": [2016, 2025],
  "audience": "Brazilian health policymakers",
  "language": "pt-BR",
  "data_sources": ["data/sih/RDSP*.parquet"],
  "domain_priors": [
    "Older patients have higher mortality",
    "COVID caused a spike in respiratory mortality"
  ],
  "analysis_steps": [
    {
      "name": "overview",
      "description": "Load J96 data and compute overall volume and mortality",
      "output_type": "metric",
      "decomposition": "time"
    },
    {
      "name": "age_decomposition",
      "description": "Decompose mortality by age group",
      "output_type": "chart",
      "decomposition": "age"
    },
    {
      "name": "geographic_variation",
      "description": "Compare mortality across municipalities",
      "output_type": "chart",
      "decomposition": "geography"
    }
  ]
}
"""


def test_parse_plan_from_json():
    plan = _parse_plan(SAMPLE_PLAN_JSON, "Why is J96 mortality rising?")

    assert plan.question == "Why is J96 mortality rising?"
    assert plan.icd10_prefix == "J96"
    assert plan.uf == "SP"
    assert plan.year_range == (2016, 2025)
    assert len(plan.analysis_steps) == 3
    assert plan.analysis_steps[0].name == "overview"
    assert len(plan.domain_priors) == 2


def test_parse_plan_with_markdown_wrapping():
    wrapped = f"```json\n{SAMPLE_PLAN_JSON}\n```"
    plan = _parse_plan(wrapped, "test question")

    assert plan.icd10_prefix == "J96"
    assert len(plan.analysis_steps) == 3


def test_parse_plan_with_thinking_tags():
    with_thinking = (
        "<think>Let me analyze this...</think>\n" + SAMPLE_PLAN_JSON
    )
    plan = _parse_plan(with_thinking, "test question")

    assert plan.icd10_prefix == "J96"


def test_parse_plan_defaults():
    minimal_json = """\
{
  "icd10_prefix": "N20",
  "analysis_steps": [
    {"name": "overview", "description": "Load data"}
  ]
}
"""
    plan = _parse_plan(minimal_json, "kidney stones")

    assert plan.uf == "SP"
    assert plan.year_range == (2016, 2025)
    assert plan.audience == "Brazilian health policymakers"
    assert plan.language == "pt-BR"


def test_planner_creates_plan_with_mock_llm():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content=SAMPLE_PLAN_JSON)

    skill = SkillContext(raw_content="# SUS Skill\nSome knowledge.")
    planner = Planner(mock_llm, skill=skill)

    plan = planner.create_plan("Why is J96 mortality rising?")

    assert plan.icd10_prefix == "J96"
    assert len(plan.analysis_steps) == 3
    mock_llm.invoke.assert_called_once()

    # Verify skill content was included in the system prompt
    call_args = mock_llm.invoke.call_args[0][0]
    system_msg = call_args[0]
    assert "SUS Domain Knowledge" in system_msg.content


def test_planner_works_without_skill():
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content=SAMPLE_PLAN_JSON)

    planner = Planner(mock_llm, skill=None)
    plan = planner.create_plan("test question")

    assert plan.icd10_prefix == "J96"


def test_analysis_step_defaults():
    step = AnalysisStep(name="test", description="do stuff")

    assert step.output_type == "chart"
    assert step.decomposition == ""


def test_investigation_plan_defaults():
    plan = InvestigationPlan(question="test", icd10_prefix="J96")

    assert plan.uf == "SP"
    assert plan.year_range == (2016, 2025)
    assert plan.analysis_steps == []
    assert plan.domain_priors == []

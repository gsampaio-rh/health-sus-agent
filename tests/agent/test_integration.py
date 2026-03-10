"""Integration test — Sprint 0 end-to-end: J96 mortality by year.

Requires:
- Respiratory failure parquet at the expected path
- An LLM provider configured (or use MockLLM for CI)

This test validates the full pipeline: engine executes analysis code,
produces a chart and metrics, and the critic evaluates the output.
"""

import json
from pathlib import Path

import pytest

from src.agent.accumulator import FindingsAccumulator
from src.agent.critic import Critic
from src.agent.engine import AnalysisEngine
from src.agent.state import CriticDecision, Finding, FindingConfidence

DATA_PATH = Path("experiments/respiratory_failure/outputs/data/resp_failure_sih.parquet")

MOCK_CRITIC_RESPONSE = json.dumps({
    "verdicts": [
        {
            "test_name": "circularity",
            "passed": True,
            "reasoning": "Not tautological",
        },
        {
            "test_name": "depth",
            "passed": True,
            "reasoning": "Decomposes by year with pre/post-COVID",
        },
        {
            "test_name": "surprise",
            "passed": True,
            "reasoning": "Post-COVID persistence is noteworthy",
        },
        {
            "test_name": "confounders",
            "passed": True,
            "reasoning": "Age not yet controlled but OK for EDA",
        },
        {
            "test_name": "so_what",
            "passed": True,
            "reasoning": "Implies structural care changes needed",
        },
    ],
    "decision": "pass",
    "summary": "Solid initial mortality trend analysis.",
    "suggestions": [],
})


class MockLLM:
    def invoke(self, messages):
        class Resp:
            content = MOCK_CRITIC_RESPONSE
        return Resp()


@pytest.fixture
def output_dir(tmp_path):
    return tmp_path / "sprint0_test"


@pytest.mark.skipif(not DATA_PATH.exists(), reason="J96 parquet not available")
def test_sprint0_engine_produces_chart_and_metrics(output_dir):
    """Verify the engine executes the mortality analysis and produces artifacts."""
    engine = AnalysisEngine(output_dir=output_dir)

    code = f"""\
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_parquet("{DATA_PATH}")
df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df = df[df["year"] >= 2016].copy()

yearly = df.groupby("year").agg(
    admissions=("MORTE", "count"),
    deaths=("MORTE", "sum"),
).reset_index()
yearly["mortality_rate"] = (yearly["deaths"] / yearly["admissions"] * 100).round(2)

overall_rate = df["MORTE"].mean() * 100
print(f"Overall mortality: {{overall_rate:.1f}}%")
print(f"Records: {{len(df)}}")

fig, ax = plt.subplots()
ax.plot(yearly["year"], yearly["mortality_rate"], marker="o")
ax.set_title("J96 Mortality Rate by Year")
save_plot(fig, "mortality_trend")

save_metrics({{
    "overall_mortality_pct": round(overall_rate, 2),
    "total_records": len(df),
}}, "mortality_trend")
"""
    result = engine.execute(code, node="eda_mortality_trend")

    assert result.error is None, f"Execution failed: {result.error}"
    assert len(result.artifacts) == 2

    plot_path = next(a for a in result.artifacts if a.endswith(".png"))
    metrics_path = next(a for a in result.artifacts if a.endswith(".json"))
    assert Path(plot_path).exists()
    assert Path(metrics_path).exists()

    with open(metrics_path) as f:
        metrics = json.load(f)
    assert 25 < metrics["overall_mortality_pct"] < 45, (
        f"Expected ~33% mortality, got {metrics['overall_mortality_pct']}%"
    )


@pytest.mark.skipif(not DATA_PATH.exists(), reason="J96 parquet not available")
def test_sprint0_full_loop_with_mock_critic(output_dir):
    """Full Sprint 0 loop: engine -> critic -> accumulator."""
    engine = AnalysisEngine(output_dir=output_dir)
    critic = Critic(llm=MockLLM())
    accumulator = FindingsAccumulator()

    code = f"""\
import pandas as pd

df = pd.read_parquet("{DATA_PATH}")
df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df = df[df["year"] >= 2016].copy()

overall = df["MORTE"].mean() * 100
pre = df[df["year"] <= 2019]["MORTE"].mean() * 100
post = df[df["year"] >= 2022]["MORTE"].mean() * 100

print(f"Overall mortality: {{overall:.1f}}%")
print(f"Pre-COVID: {{pre:.1f}}%")
print(f"Post-COVID: {{post:.1f}}%")
print(f"Change: +{{post - pre:.1f}}pp")
"""
    result = engine.execute(code, node="eda_mortality_trend")
    assert result.error is None

    reflection = critic.evaluate(result, findings_summary=accumulator.summary())
    assert reflection.decision == CriticDecision.PASS

    finding = Finding(
        id="mortality_trend_01",
        statement="J96 mortality rose post-COVID",
        evidence=result.output,
        so_what="Structural care changes needed",
        confidence=FindingConfidence.HIGH,
        source_node="eda_mortality_trend",
    )
    accumulator.add_finding(finding)

    assert len(accumulator.facts) == 1
    assert "mortality" in accumulator.summary().lower()

"""Sprint 0 runner — hardcoded plan -> engine -> critic -> accumulator.

Demonstrates the core loop with a single analysis step: compute J96
mortality trend by year. No LangGraph, no LLM planning — just function
calls to validate the pipeline end-to-end.
"""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from src.agent.accumulator import FindingsAccumulator
from src.agent.config import AgentConfig, get_llm
from src.agent.critic import Critic
from src.agent.engine import AnalysisEngine
from src.agent.state import (
    CriticDecision,
    Finding,
    FindingConfidence,
    InvestigationState,
)

MORTALITY_TREND_CODE = '''\
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_parquet("{data_path}")
df["MORTE"] = pd.to_numeric(df["MORTE"], errors="coerce").fillna(0).astype(int)
df["year"] = pd.to_numeric(df["year"], errors="coerce")

# Filter to 2016+ (consistent data coverage)
df = df[df["year"] >= 2016].copy()

yearly = df.groupby("year").agg(
    admissions=("MORTE", "count"),
    deaths=("MORTE", "sum"),
).reset_index()
yearly["mortality_rate"] = (yearly["deaths"] / yearly["admissions"] * 100).round(2)

print("=== J96 Respiratory Failure: Mortality by Year (SP) ===")
print(yearly.to_string(index=False))
print()

overall_rate = df["MORTE"].mean() * 100
print(f"Overall mortality rate: {{overall_rate:.1f}}%")
print(f"Total admissions: {{len(df):,}}")
print(f"Total deaths: {{df['MORTE'].sum():,}}")

# Trend: pre-COVID vs post-COVID
pre = yearly[yearly["year"] <= 2019]["mortality_rate"].mean()
post = yearly[yearly["year"] >= 2022]["mortality_rate"].mean()
print(f"\\nPre-COVID avg mortality (2016-2019): {{pre:.1f}}%")
print(f"Post-COVID avg mortality (2022-2025): {{post:.1f}}%")
print(f"Change: +{{post - pre:.1f}}pp")

# Plot
fig, ax1 = plt.subplots(figsize=(12, 6))

color_volume = "#2563EB"
color_mortality = "#DC2626"

ax1.bar(yearly["year"], yearly["admissions"], color=color_volume, alpha=0.6, label="Admissions")
ax1.set_xlabel("Year")
ax1.set_ylabel("Admissions", color=color_volume)
ax1.tick_params(axis="y", labelcolor=color_volume)

ax2 = ax1.twinx()
ax2.plot(yearly["year"], yearly["mortality_rate"], color=color_mortality,
         marker="o", linewidth=2.5, label="Mortality %")
ax2.set_ylabel("Mortality Rate (%)", color=color_mortality)
ax2.tick_params(axis="y", labelcolor=color_mortality)

ax1.set_title("J96 Respiratory Failure — Admissions & Mortality Rate (São Paulo)")
fig.legend(loc="upper left", bbox_to_anchor=(0.12, 0.88))
fig.tight_layout()

save_plot(fig, "mortality_trend_by_year")

save_metrics({{
    "overall_mortality_rate_pct": round(overall_rate, 2),
    "total_admissions": int(len(df)),
    "total_deaths": int(df["MORTE"].sum()),
    "pre_covid_avg_mortality_pct": round(pre, 2),
    "post_covid_avg_mortality_pct": round(post, 2),
    "mortality_change_pp": round(post - pre, 2),
    "yearly": yearly.to_dict(orient="records"),
}}, "mortality_trend")

print("\\nDone. Chart and metrics saved.")
'''


def run_sprint0(
    data_path: str | Path,
    output_dir: str | Path,
    config: AgentConfig | None = None,
) -> InvestigationState:
    """Run the Sprint 0 core loop: one analysis step + critic evaluation."""
    config = config or AgentConfig()
    data_path = Path(data_path)
    output_dir = Path(output_dir)

    state = InvestigationState(
        research_question="Why is respiratory failure mortality rising in São Paulo?",
        icd10_prefix="J96",
        uf="SP",
        year_range=(2016, 2025),
        data_dir=str(data_path.parent),
        output_dir=str(output_dir),
    )

    engine = AnalysisEngine(
        output_dir=output_dir,
        timeout_seconds=config.repl_timeout_seconds,
        max_output_chars=config.repl_max_output_chars,
    )
    llm = get_llm(config)
    critic = Critic(llm=llm)
    accumulator = FindingsAccumulator()

    # --- Step 1: Execute the hardcoded mortality trend analysis ---
    state.current_step = "eda_mortality_trend"
    code = MORTALITY_TREND_CODE.format(data_path=str(data_path))

    logger.info("Executing analysis: {}", state.current_step)
    result = engine.execute(code, node=state.current_step)
    state.trace.append(result)

    if result.error:
        logger.error("Execution failed: {}", result.error)
        state.errors.append(result.error)
        return state

    logger.info("Execution OK ({}ms). Artifacts: {}", result.duration_ms, result.artifacts)

    # --- Step 2: Critic evaluation ---
    logger.info("Running critic evaluation...")
    reflection = critic.evaluate(result, findings_summary=accumulator.summary())
    state.reflections.append(reflection)

    logger.info("Critic decision: {} — {}", reflection.decision.value, reflection.summary)
    for v in reflection.verdicts:
        status = "PASS" if v.passed else "FAIL"
        logger.info("  [{}] {}: {}", status, v.test_name, v.reasoning)

    # --- Step 3: Update accumulator based on critic ---
    if reflection.decision == CriticDecision.PASS:
        finding = Finding(
            id="mortality_trend_01",
            statement="J96 respiratory failure mortality rose post-COVID",
            evidence=result.output[:500],
            so_what="Post-COVID mortality remains elevated, suggesting structural changes in care",
            confidence=FindingConfidence.HIGH,
            source_node=state.current_step,
        )
        accumulator.add_finding(finding)
        state.findings = list(accumulator.facts)
        logger.info("Finding added to accumulator")
    elif reflection.decision == CriticDecision.DEEPEN:
        for suggestion in reflection.suggestions:
            accumulator.add_open_question(suggestion)
        state.open_questions = list(accumulator.open_questions)
        logger.info("Critic suggests deepening: {}", reflection.suggestions)
    else:
        state.errors.append(f"Critic rejected analysis: {reflection.summary}")
        logger.warning("Analysis rejected by critic")

    return state


if __name__ == "__main__":
    import sys

    data = sys.argv[1] if len(sys.argv) > 1 else (
        "experiments/respiratory_failure/outputs/data/resp_failure_sih.parquet"
    )
    out = sys.argv[2] if len(sys.argv) > 2 else "outputs/sprint0"

    state = run_sprint0(data_path=data, output_dir=out)
    print(f"\nFinal state: {len(state.findings)} findings, {len(state.errors)} errors")

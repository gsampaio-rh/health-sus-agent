"""Critic evaluation runner.

Evaluates the Critic against the 20-case dataset and reports per-test
accuracy, decision accuracy, and misclassified cases.

Usage:
    # With Ollama
    AGENT_LLM_PROVIDER=openai \
    AGENT_LLM_BASE_URL=http://localhost:11434/v1 \
    AGENT_LLM_MODEL=gemma3:12b-it-q8_0 \
    AGENT_LLM_API_KEY=not-needed \
    python -m eval.run_critic_eval

    # With Anthropic
    AGENT_LLM_PROVIDER=anthropic \
    python -m eval.run_critic_eval
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from loguru import logger

from eval.critic_dataset import EVAL_CASES, EvalCase
from src.agent.config import AgentConfig, get_llm
from src.agent.critic import Critic
from src.agent.state import CodeExecution, CriticDecision, Reflection

RESULTS_DIR = Path("eval/results")
ALL_TESTS = ["circularity", "depth", "surprise", "confounders", "so_what"]


@dataclass
class CaseResult:
    case_id: str
    category: str
    expected_decision: str
    actual_decision: str
    decision_correct: bool
    expected_failures: list[str]
    actual_failures: list[str]
    per_test_correct: dict[str, bool]
    summary: str
    duration_ms: int


@dataclass
class EvalReport:
    model: str
    total_cases: int
    decision_accuracy: float
    per_test_accuracy: dict[str, float]
    overall_test_accuracy: float
    misclassified: list[str]
    case_results: list[CaseResult]
    total_duration_ms: int


def _run_single_case(critic: Critic, case: EvalCase) -> CaseResult:
    """Evaluate a single case and return the result."""
    execution = CodeExecution(
        node=f"eval_{case.id}",
        code=case.code,
        output=case.output,
        artifacts=case.artifacts,
    )

    start = time.perf_counter_ns()
    try:
        reflection = critic.evaluate(execution, findings_summary=case.findings_context)
    except Exception as e:
        logger.error("Case {} failed with error: {}", case.id, e)
        reflection = Reflection(
            phase="critic",
            verdicts=[],
            decision=CriticDecision.FAIL,
            summary=f"Error: {e}",
        )
    duration_ms = int((time.perf_counter_ns() - start) / 1_000_000)

    actual_decision = reflection.decision
    decision_correct = actual_decision == case.expected_decision

    actual_failures = [v.test_name for v in reflection.verdicts if not v.passed]

    per_test_correct: dict[str, bool] = {}
    for test in ALL_TESTS:
        expected_fail = test in case.expected_failures
        actual_fail = test in actual_failures
        per_test_correct[test] = expected_fail == actual_fail

    return CaseResult(
        case_id=case.id,
        category=case.category,
        expected_decision=case.expected_decision.value,
        actual_decision=actual_decision.value,
        decision_correct=decision_correct,
        expected_failures=case.expected_failures,
        actual_failures=actual_failures,
        per_test_correct=per_test_correct,
        summary=reflection.summary,
        duration_ms=duration_ms,
    )


def run_evaluation(config: AgentConfig | None = None) -> EvalReport:
    """Run the full evaluation suite."""
    config = config or AgentConfig()
    llm = get_llm(config)
    critic = Critic(llm=llm)

    model_name = config.resolved_model
    logger.info("Starting evaluation with model: {}", model_name)
    logger.info("Cases: {}", len(EVAL_CASES))

    results: list[CaseResult] = []
    total_start = time.perf_counter_ns()

    for i, case in enumerate(EVAL_CASES, 1):
        logger.info("[{}/{}] {} — {}", i, len(EVAL_CASES), case.id, case.description)
        result = _run_single_case(critic, case)
        results.append(result)

        status = "OK" if result.decision_correct else "MISS"
        logger.info(
            "  [{}] expected={} actual={} ({}ms)",
            status,
            result.expected_decision,
            result.actual_decision,
            result.duration_ms,
        )

    total_duration_ms = int((time.perf_counter_ns() - total_start) / 1_000_000)

    n_decision_correct = sum(1 for r in results if r.decision_correct)
    decision_accuracy = n_decision_correct / len(results)

    per_test_accuracy: dict[str, float] = {}
    for test in ALL_TESTS:
        correct = sum(1 for r in results if r.per_test_correct.get(test, False))
        per_test_accuracy[test] = correct / len(results)

    all_test_checks = sum(len(r.per_test_correct) for r in results)
    all_test_correct = sum(
        sum(1 for v in r.per_test_correct.values() if v) for r in results
    )
    overall_test_accuracy = all_test_correct / all_test_checks if all_test_checks else 0

    misclassified = [
        f"{r.case_id}: expected {r.expected_decision}, "
        f"got {r.actual_decision} — {r.summary[:80]}"
        for r in results
        if not r.decision_correct
    ]

    return EvalReport(
        model=model_name,
        total_cases=len(results),
        decision_accuracy=decision_accuracy,
        per_test_accuracy=per_test_accuracy,
        overall_test_accuracy=overall_test_accuracy,
        misclassified=misclassified,
        case_results=results,
        total_duration_ms=total_duration_ms,
    )


def print_report(report: EvalReport) -> None:
    """Print a formatted evaluation report."""
    print()
    print("=" * 60)
    print("Critic Evaluation Report")
    print("=" * 60)
    print(f"Model:       {report.model}")
    print(f"Cases:       {report.total_cases}")
    print(f"Duration:    {report.total_duration_ms / 1000:.1f}s")
    print()

    n_correct = int(report.decision_accuracy * report.total_cases)
    print(f"Decision accuracy:     {report.decision_accuracy:.1%} "
          f"({n_correct}/{report.total_cases})")
    print(f"Per-test accuracy:     {report.overall_test_accuracy:.1%}")
    print()

    print("Per-test breakdown:")
    for test, acc in report.per_test_accuracy.items():
        n = int(acc * report.total_cases)
        bar = "#" * int(acc * 20) + "." * (20 - int(acc * 20))
        print(f"  {test:15s}  {acc:5.1%}  ({n:2d}/{report.total_cases})  [{bar}]")
    print()

    # Category breakdown
    categories: dict[str, list[CaseResult]] = {}
    for r in report.case_results:
        categories.setdefault(r.category, []).append(r)

    print("Per-category breakdown:")
    for cat, case_results in categories.items():
        correct = sum(1 for r in case_results if r.decision_correct)
        total = len(case_results)
        print(f"  {cat:20s}  {correct}/{total}")
    print()

    if report.misclassified:
        print(f"Misclassified ({len(report.misclassified)}):")
        for line in report.misclassified:
            print(f"  {line}")
    else:
        print("No misclassified cases.")
    print()
    print("=" * 60)


def save_report(report: EvalReport) -> Path:
    """Save raw results to JSON."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    model_slug = report.model.replace(":", "_").replace("/", "_")
    path = RESULTS_DIR / f"eval_{model_slug}_{timestamp}.json"

    data = {
        "model": report.model,
        "total_cases": report.total_cases,
        "decision_accuracy": report.decision_accuracy,
        "per_test_accuracy": report.per_test_accuracy,
        "overall_test_accuracy": report.overall_test_accuracy,
        "misclassified": report.misclassified,
        "total_duration_ms": report.total_duration_ms,
        "case_results": [asdict(r) for r in report.case_results],
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    logger.info("Results saved to {}", path)
    return path


if __name__ == "__main__":
    config = AgentConfig()
    report = run_evaluation(config)
    print_report(report)
    save_report(report)

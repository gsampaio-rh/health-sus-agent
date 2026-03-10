"""Compare Critic eval results across models.

Reads all JSON files in eval/results/ and produces a side-by-side
comparison table. Groups by model, uses the latest run per model.

Usage:
    python -m eval.compare_results
"""

from __future__ import annotations

import json
from pathlib import Path

RESULTS_DIR = Path("eval/results")
ALL_TESTS = ["circularity", "depth", "surprise", "confounders", "so_what"]


def load_latest_per_model() -> dict[str, dict]:
    """Load the most recent result file for each model."""
    files = sorted(RESULTS_DIR.glob("eval_*.json"))
    if not files:
        print("No result files found in eval/results/")
        return {}

    by_model: dict[str, Path] = {}
    for f in files:
        data = json.loads(f.read_text())
        model = data["model"]
        by_model[model] = f

    results = {}
    for model, path in by_model.items():
        results[model] = json.loads(path.read_text())
    return results


def compute_precision_recall(case_results: list[dict]) -> dict[str, dict]:
    """Compute per-test precision and recall."""
    metrics: dict[str, dict] = {}
    for test in ALL_TESTS:
        tp = fp = fn = tn = 0
        for r in case_results:
            expected = test in r["expected_failures"]
            actual = test in r["actual_failures"]
            if expected and actual:
                tp += 1
            elif not expected and actual:
                fp += 1
            elif expected and not actual:
                fn += 1
            else:
                tn += 1
        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = (2 * precision * recall / (precision + recall)
              if (precision + recall) > 0 else 0.0)
        metrics[test] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        }
    return metrics


def print_comparison(results: dict[str, dict]) -> None:
    models = list(results.keys())
    if not models:
        return

    col_w = max(len(m) for m in models)
    col_w = max(col_w, 12)

    header = f"{'Metric':<25s}"
    for m in models:
        header += f"  {m:>{col_w}s}"
    sep = "-" * len(header)

    print()
    print("=" * len(header))
    print("Critic Eval — Model Comparison")
    print("=" * len(header))
    print()
    print(header)
    print(sep)

    # Decision accuracy
    row = f"{'Decision accuracy':<25s}"
    for m in models:
        acc = results[m]["decision_accuracy"]
        row += f"  {acc:>{col_w}.1%}"
    print(row)

    # Per-test accuracy
    row = f"{'Overall test accuracy':<25s}"
    for m in models:
        acc = results[m]["overall_test_accuracy"]
        row += f"  {acc:>{col_w}.1%}"
    print(row)

    print(sep)

    # Per-test breakdown
    for test in ALL_TESTS:
        row = f"  {test:<23s}"
        for m in models:
            acc = results[m]["per_test_accuracy"].get(test, 0)
            row += f"  {acc:>{col_w}.1%}"
        print(row)

    print(sep)

    # Precision / recall (computed from case_results)
    print()
    print("Per-test precision (flagging only genuine failures):")
    model_metrics = {
        m: compute_precision_recall(results[m]["case_results"])
        for m in models
    }
    for test in ALL_TESTS:
        row = f"  {test:<23s}"
        for m in models:
            p = model_metrics[m][test]["precision"]
            row += f"  {p:>{col_w}.0%}"
        print(row)

    print()
    print("Per-test recall (catching actual failures):")
    for test in ALL_TESTS:
        row = f"  {test:<23s}"
        for m in models:
            r = model_metrics[m][test]["recall"]
            row += f"  {r:>{col_w}.0%}"
        print(row)

    print()
    print("Per-test F1:")
    for test in ALL_TESTS:
        row = f"  {test:<23s}"
        for m in models:
            f1 = model_metrics[m][test]["f1"]
            row += f"  {f1:>{col_w}.0%}"
        print(row)

    # Category breakdown
    print()
    print(sep)
    categories = ["pass", "fail_circularity", "fail_depth",
                   "fail_surprise", "fail_confounders", "fail_so_what"]
    print("Per-category decision accuracy:")
    for cat in categories:
        row = f"  {cat:<23s}"
        for m in models:
            cat_results = [
                r for r in results[m]["case_results"] if r["category"] == cat
            ]
            if cat_results:
                correct = sum(1 for r in cat_results if r["decision_correct"])
                total = len(cat_results)
                row += f"  {f'{correct}/{total}':>{col_w}s}"
            else:
                row += f"  {'N/A':>{col_w}s}"
        print(row)

    # Duration
    print()
    row = f"{'Duration (s)':<25s}"
    for m in models:
        dur = results[m]["total_duration_ms"] / 1000
        row += f"  {dur:>{col_w}.0f}"
    print(row)

    # Misclassified count
    row = f"{'Misclassified':<25s}"
    for m in models:
        n = len(results[m]["misclassified"])
        row += f"  {n:>{col_w}d}"
    print(row)

    print()
    print("=" * len(header))


if __name__ == "__main__":
    results = load_latest_per_model()
    print_comparison(results)

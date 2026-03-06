"""H2 — Dengue Epidemic Early Warning experiment runner."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger
from rich.console import Console
from rich.table import Table

from src.experiments.h2_dengue.data_loader import (
    add_epidemic_label,
    build_weekly_series,
    load_dengue_sp,
)
from src.experiments.h2_dengue.feature_engineering import (
    FEATURE_COLUMNS,
    build_feature_matrix,
)
from src.experiments.h2_dengue.models import (
    majority_class_baseline,
    seasonal_naive_baseline,
    train_lightgbm,
    train_xgboost,
    ModelResult,
)
from src.experiments.h2_dengue.evaluation import (
    evaluate_model,
    format_report,
    EvaluationReport,
)

SINAN_DATA_DIR = Path("data/sinan")
OUTPUT_DIR = Path("analysis/h2_dengue")
HORIZONS = [4, 8]

console = Console()


def temporal_split(df: pd.DataFrame, horizon: int):
    """Split data temporally: train 2017-2023, validate 2024, test 2025."""
    target_col = f"target_epidemic_{horizon}w"

    train = df[(df["epi_year"] >= 2017) & (df["epi_year"] <= 2023)].copy()
    validate = df[df["epi_year"] == 2024].copy()
    test = df[df["epi_year"] == 2025].copy()

    train = train.dropna(subset=FEATURE_COLUMNS + [target_col])
    validate = validate.dropna(subset=FEATURE_COLUMNS + [target_col])
    test = test.dropna(subset=FEATURE_COLUMNS + [target_col])

    return train, validate, test


def run_experiment():
    console.print("\n[bold cyan]═══ H2: Dengue Epidemic Early Warning ═══[/bold cyan]\n")

    # 1. Load data
    console.print("[bold]Step 1:[/bold] Loading dengue data...")
    confirmed = load_dengue_sp(SINAN_DATA_DIR)
    weekly = build_weekly_series(confirmed, min_cases_total=500)
    weekly = add_epidemic_label(weekly, threshold_per_100k=300.0)

    console.print(f"  Municipalities: {weekly['municipality'].nunique()}")
    console.print(f"  Weeks: {len(weekly):,}")
    console.print(f"  Epidemic prevalence: {weekly['is_epidemic'].mean():.1%}\n")

    all_reports: list[EvaluationReport] = []
    all_predictions: list[dict] = []

    for horizon in HORIZONS:
        console.print(f"[bold]Step 2:[/bold] Feature engineering (horizon={horizon}w)...")
        featured = build_feature_matrix(weekly, horizon=horizon)

        train, validate, test = temporal_split(featured, horizon)
        target_col = f"target_epidemic_{horizon}w"

        X_train = train[FEATURE_COLUMNS].fillna(0)
        y_train = train[target_col].astype(int).values
        X_val = validate[FEATURE_COLUMNS].fillna(0)
        y_val = validate[target_col].astype(int).values

        console.print(f"  Train: {len(train):,} rows ({y_train.sum():,} epidemic)")
        console.print(f"  Validate: {len(validate):,} rows ({y_val.sum():,} epidemic)")

        if len(test) > 0:
            X_test = test[FEATURE_COLUMNS].fillna(0)
            y_test = test[target_col].astype(int).values
            console.print(f"  Test: {len(test):,} rows ({y_test.sum():,} epidemic)")
        else:
            console.print("  [yellow]Test set empty (2025 data may be incomplete)[/yellow]")
            X_test, y_test = X_val, y_val

        # 3. Baselines
        console.print(f"\n[bold]Step 3:[/bold] Running baselines (horizon={horizon}w)...")
        results: list[ModelResult] = []

        mc = majority_class_baseline(y_train, y_val)
        results.append(mc)

        sn = seasonal_naive_baseline(train, validate, horizon)
        results.append(sn)

        # 4. ML models
        console.print(f"[bold]Step 4:[/bold] Training ML models (horizon={horizon}w)...")

        lgbm_result = train_lightgbm(X_train, y_train, X_val, y_val)
        results.append(lgbm_result)

        xgb_result = train_xgboost(X_train, y_train, X_val, y_val)
        results.append(xgb_result)

        # 5. Evaluate
        console.print(f"\n[bold]Step 5:[/bold] Evaluation (horizon={horizon}w)...")
        for result in results:
            report = evaluate_model(result, horizon)
            all_reports.append(report)
            console.print(f"\n{format_report(report)}")

            for i in range(len(result.y_true)):
                all_predictions.append({
                    "model": result.name,
                    "horizon": horizon,
                    "y_true": int(result.y_true[i]),
                    "y_pred": int(result.y_pred[i]),
                    "y_prob": float(result.y_prob[i]) if result.y_prob is not None else None,
                })

    # Summary table
    console.print("\n")
    _print_summary_table(all_reports)

    # Save results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _save_predictions(all_predictions)
    _save_reports(all_reports)

    console.print(f"\n[green]Results saved to {OUTPUT_DIR}/[/green]")


def _print_summary_table(reports: list[EvaluationReport]):
    table = Table(title="H2 Results Summary — Dengue Epidemic Early Warning (SP)")
    table.add_column("Model", style="cyan")
    table.add_column("Horizon", justify="center")
    table.add_column("F1", justify="right")
    table.add_column("Precision", justify="right")
    table.add_column("Recall", justify="right")
    table.add_column("AUC-ROC", justify="right")

    for r in reports:
        f1_str = f"{r.f1.value:.3f}"
        prec_str = f"{r.precision.value:.3f}"
        rec_str = f"{r.recall.value:.3f}"
        auc_str = f"{r.auc_roc.value:.3f}"

        if r.f1.value >= 0.7:
            f1_str = f"[bold green]{f1_str}[/bold green]"
        elif r.f1.value >= 0.5:
            f1_str = f"[yellow]{f1_str}[/yellow]"

        table.add_row(r.model_name, f"{r.horizon}w", f1_str, prec_str, rec_str, auc_str)

    console.print(table)


def _save_predictions(predictions: list[dict]):
    path = OUTPUT_DIR / "predictions.jsonl"
    with open(path, "w") as f:
        for pred in predictions:
            f.write(json.dumps(pred) + "\n")


def _save_reports(reports: list[EvaluationReport]):
    path = OUTPUT_DIR / "metrics.json"
    metrics = []
    for r in reports:
        metrics.append({
            "model": r.model_name,
            "horizon": r.horizon,
            "f1": r.f1.value,
            "f1_ci": [r.f1.ci_lower, r.f1.ci_upper],
            "precision": r.precision.value,
            "precision_ci": [r.precision.ci_lower, r.precision.ci_upper],
            "recall": r.recall.value,
            "recall_ci": [r.recall.ci_lower, r.recall.ci_upper],
            "auc_roc": r.auc_roc.value,
            "auc_roc_ci": [r.auc_roc.ci_lower, r.auc_roc.ci_upper],
            "auc_pr": r.auc_pr.value,
            "n_samples": r.n_samples,
            "epidemic_prevalence": r.epidemic_prevalence,
        })

    with open(path, "w") as f:
        json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    run_experiment()

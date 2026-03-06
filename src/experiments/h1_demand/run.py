"""H1 — Hospital Bed Demand Forecasting experiment runner."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table

from src.experiments.h1_demand.data_loader import (
    build_monthly_demand,
    load_cnes_beds,
    load_sih_admissions,
)
from src.experiments.h1_demand.feature_engineering import (
    FEATURE_COLUMNS,
    FEATURE_COLUMNS_WITH_BEDS,
    build_feature_matrix,
)
from src.experiments.h1_demand.models import (
    historical_mean_forecast,
    seasonal_naive_forecast,
    train_lightgbm_regressor,
)
from src.experiments.h1_demand.evaluation import (
    evaluate_forecast,
    format_report,
    ForecastReport,
)

SIH_DIR = Path("data/sih")
CNES_DIR = Path("data/cnes")
OUTPUT_DIR = Path("analysis/h1_demand")

console = Console()

TOP_N_MUNICIPALITIES = 50
MIN_MONTHLY_RECORDS = 50
GROUP_COLS = ["municipality", "espec"]


def filter_top_series(demand: pd.DataFrame) -> pd.DataFrame:
    """Keep only municipality × specialty combos with enough data for modeling."""
    series_totals = demand.groupby(GROUP_COLS)["admissions"].sum()
    valid = series_totals[series_totals >= MIN_MONTHLY_RECORDS * 12].index
    filtered = demand.set_index(GROUP_COLS).loc[valid].reset_index()

    console.print(
        f"  Filtered to {filtered[GROUP_COLS[0]].nunique()} municipalities × "
        f"{filtered[GROUP_COLS[1]].nunique()} specialties "
        f"({len(valid):,} series with ≥{MIN_MONTHLY_RECORDS}/month avg)"
    )
    return filtered


def run_experiment():
    console.print("\n[bold cyan]═══ H1: Hospital Bed Demand Forecasting ═══[/bold cyan]\n")

    # 1. Load data
    console.print("[bold]Step 1:[/bold] Loading SIH admissions...")
    sih = load_sih_admissions(SIH_DIR)
    demand = build_monthly_demand(sih)
    demand = filter_top_series(demand)

    console.print("\n[bold]Step 2:[/bold] Loading CNES bed capacity...")
    beds = load_cnes_beds(CNES_DIR)

    # 3. Feature engineering
    console.print("\n[bold]Step 3:[/bold] Feature engineering...")
    featured = build_feature_matrix(demand, beds=beds, group_cols=GROUP_COLS)

    # Also build state-level aggregation for a cleaner signal
    state_demand = (
        demand.groupby(["year", "month", "espec"])
        .agg(
            admissions=("admissions", "sum"),
            total_bed_days=("total_bed_days", "sum"),
            deaths=("deaths", "sum"),
            total_value=("total_value", "sum"),
        )
        .reset_index()
    )
    state_demand["municipality"] = "SP_TOTAL"
    state_demand["espec_name"] = state_demand["espec"].map(
        {"01": "Cirurgia", "02": "Obstetrícia", "03": "Clínica Médica", "07": "Pediatria"}
    ).fillna("Outro")

    state_beds = (
        beds.groupby(["year", "month"])
        .agg(
            beds_surgical=("beds_surgical", "sum"),
            beds_clinical=("beds_clinical", "sum"),
            beds_obstetric=("beds_obstetric", "sum"),
            beds_total_sus=("beds_total_sus", "sum"),
            n_facilities=("n_facilities", "sum"),
        )
        .reset_index()
    )
    state_beds["municipality"] = "SP_TOTAL"

    state_featured = build_feature_matrix(
        state_demand, beds=state_beds, group_cols=["municipality", "espec"]
    )

    console.print(f"  Municipality-level: {len(featured):,} rows")
    console.print(f"  State-level: {len(state_featured):,} rows")

    # 4. Train/test split (temporal)
    console.print("\n[bold]Step 4:[/bold] Training models...")
    all_reports: list[ForecastReport] = []

    for level_name, df, use_beds in [
        ("State (SP)", state_featured, True),
        ("Municipality", featured, True),
    ]:
        console.print(f"\n  [bold]--- {level_name} level ---[/bold]")

        train = df[(df["year"] >= 2017) & (df["year"] <= 2023)].copy()
        test = df[df["year"] == 2024].copy()

        feat_cols = FEATURE_COLUMNS_WITH_BEDS if use_beds else FEATURE_COLUMNS
        available_cols = [c for c in feat_cols if c in train.columns]

        train_clean = train.dropna(subset=available_cols + ["admissions"])
        test_clean = test.dropna(subset=available_cols + ["admissions"])

        if len(test_clean) == 0:
            console.print(f"  [yellow]No test data for {level_name}[/yellow]")
            continue

        X_train = train_clean[available_cols].fillna(0)
        y_train = train_clean["admissions"].values.astype(float)
        X_test = test_clean[available_cols].fillna(0)
        y_test = test_clean["admissions"].values.astype(float)

        console.print(f"  Train: {len(X_train):,} | Test: {len(X_test):,}")

        # Baselines
        sn = seasonal_naive_forecast(train_clean, test_clean)
        sn.name = f"{level_name} | seasonal_naive"
        report_sn = evaluate_forecast(sn)
        all_reports.append(report_sn)
        console.print(f"\n{format_report(report_sn)}")

        hm = historical_mean_forecast(train_clean, test_clean, GROUP_COLS)
        hm.name = f"{level_name} | historical_mean"
        report_hm = evaluate_forecast(hm)
        all_reports.append(report_hm)
        console.print(f"\n{format_report(report_hm)}")

        # LightGBM
        lgbm = train_lightgbm_regressor(X_train, y_train, X_test, y_test)
        lgbm.name = f"{level_name} | lightgbm"
        report_lgbm = evaluate_forecast(lgbm)
        all_reports.append(report_lgbm)
        console.print(f"\n{format_report(report_lgbm)}")

    # Summary
    console.print("\n")
    _print_summary(all_reports)
    _save_results(all_reports)
    console.print(f"\n[green]Results saved to {OUTPUT_DIR}/[/green]")


def _print_summary(reports: list[ForecastReport]):
    table = Table(title="H1 Results — Hospital Bed Demand Forecasting (SP, 2024)")
    table.add_column("Model", style="cyan")
    table.add_column("MAPE %", justify="right")
    table.add_column("MAE", justify="right")
    table.add_column("RMSE", justify="right")
    table.add_column("Within 15%", justify="right")
    table.add_column("N", justify="right")

    for r in reports:
        mape_str = f"{r.mape.value:.1f}"
        if r.mape.value < 15:
            mape_str = f"[bold green]{mape_str}[/bold green]"
        elif r.mape.value < 25:
            mape_str = f"[yellow]{mape_str}[/yellow]"

        table.add_row(
            r.model_name,
            mape_str,
            f"{r.mae.value:.1f}",
            f"{r.rmse.value:.1f}",
            f"{r.within_15pct.value:.1f}%",
            f"{r.n_samples:,}",
        )

    console.print(table)


def _save_results(reports: list[ForecastReport]):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics = []
    for r in reports:
        metrics.append({
            "model": r.model_name,
            "mape": r.mape.value,
            "mape_ci": [r.mape.ci_lower, r.mape.ci_upper],
            "rmse": r.rmse.value,
            "mae": r.mae.value,
            "within_15pct": r.within_15pct.value,
            "n_samples": r.n_samples,
            "mean_actual": r.mean_actual,
        })

    with open(OUTPUT_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    run_experiment()

"""Raio-X ML layer — demand forecasting, risk prediction, resource optimization.

Run after run.py (A1 + A7) to add the ML-powered predictive layer.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from rich.console import Console
from rich.table import Table

from src.experiments.raio_x.a1_avoidable import load_and_classify, muni_year_summary
from src.experiments.raio_x.a7_demand_supply import load_cnes_supply, load_sih_demand
from src.experiments.raio_x.ml_forecast import (
    compute_future_gap,
    optimize_allocation,
    predict_icsap_risk,
    project_future_demand,
    train_demand_forecaster,
    train_icsap_risk_model,
)

OUTPUT_DIR = Path("analysis/raio_x")
PLOT_DIR = OUTPUT_DIR / "plots"

console = Console()
sns.set_theme(style="whitegrid", font_scale=1.1)


def run_ml_pipeline():
    PLOT_DIR.mkdir(parents=True, exist_ok=True)

    # ─── 1. Demand Forecasting ─────────────────────────────────────────────
    console.print("\n[bold cyan]═══ ML: Demand Forecasting (LightGBM) ═══[/bold cyan]\n")

    console.print("[bold]Step 1:[/bold] Loading SIH demand...")
    demand = load_sih_demand()

    console.print("[bold]Step 2:[/bold] Training demand forecaster...")
    demand_model, demand_featured = train_demand_forecaster(demand)

    console.print("[bold]Step 3:[/bold] Projecting demand 2026-2028...")
    projections = project_future_demand(demand_model, demand_featured, years=[2026, 2027, 2028])

    console.print("[bold]Step 4:[/bold] Computing future bed gaps...")
    supply = load_cnes_supply()
    future_gap = compute_future_gap(projections, supply)

    # State-level future summary
    future_state = (
        future_gap.groupby(["bed_type", "year"])
        .agg(
            beds_needed=("beds_needed", "sum"),
            beds_available=("beds_available", "sum"),
            deficit=("bed_deficit", lambda x: x[x > 0].sum()),
            municipalities_in_deficit=("bed_deficit", lambda x: (x > 0).sum()),
            doctors_needed=("additional_doctors", "sum"),
        )
        .reset_index()
    )

    _print_future_demand_table(future_state)
    _plot_demand_projection(demand, projections)
    _plot_future_gap_evolution(future_state)

    # ─── 2. ICSAP Risk Model ──────────────────────────────────────────────
    console.print("\n[bold cyan]═══ ML: ICSAP Risk Prediction (LightGBM) ═══[/bold cyan]\n")

    console.print("[bold]Step 5:[/bold] Loading ICSAP data...")
    muni_agg, _ = load_and_classify()
    muni_year = muni_year_summary(muni_agg)

    # Filter to municipalities with enough data
    muni_counts = muni_year.groupby("municipality").size()
    valid_munis = muni_counts[muni_counts >= 5].index
    muni_year = muni_year[muni_year["municipality"].isin(valid_munis)]

    console.print("[bold]Step 6:[/bold] Training ICSAP risk model...")
    icsap_model, icsap_featured = train_icsap_risk_model(muni_year, supply)

    console.print("[bold]Step 7:[/bold] Predicting 2025 ICSAP risk...")
    risk = predict_icsap_risk(icsap_model, icsap_featured, target_year=2025)

    if len(risk) > 0:
        _print_icsap_risk_table(risk)
        _plot_icsap_risk(risk)
        _plot_feature_importance(icsap_model, "ICSAP Risk Model", "ml_05_icsap_importance.png")
    else:
        console.print("[yellow]No ICSAP risk predictions (insufficient data for 2025)[/yellow]")

    # ─── 3. Resource Allocation ────────────────────────────────────────────
    console.print("\n[bold cyan]═══ ML: Resource Allocation Optimizer ═══[/bold cyan]\n")

    console.print("[bold]Step 8:[/bold] Optimizing bed allocation (budget: 5,000 beds)...")
    allocation = optimize_allocation(future_gap, risk, budget_beds=5000)

    if len(allocation) > 0:
        _print_allocation_table(allocation)
        _plot_allocation(allocation)

    # ─── Save ──────────────────────────────────────────────────────────────
    _save_ml_metrics(future_state, risk, allocation)
    _plot_feature_importance(demand_model, "Demand Forecaster", "ml_04_demand_importance.png")

    console.print(f"\n[green]ML results saved to {OUTPUT_DIR}/[/green]")


def _print_future_demand_table(future_state: pd.DataFrame):
    table = Table(title="Projected Bed Deficit — São Paulo 2026-2028 (LightGBM forecast)")
    table.add_column("Year", style="cyan")
    table.add_column("Bed Type")
    table.add_column("Needed", justify="right")
    table.add_column("Available", justify="right")
    table.add_column("Deficit", justify="right")
    table.add_column("Doctors", justify="right")

    for _, row in future_state.sort_values(["year", "bed_type"]).iterrows():
        deficit = int(row["deficit"])
        deficit_str = f"{deficit:,}" if deficit > 0 else "0"
        if deficit > 1000:
            deficit_str = f"[bold red]{deficit_str}[/bold red]"
        elif deficit > 0:
            deficit_str = f"[yellow]{deficit_str}[/yellow]"

        table.add_row(
            str(int(row["year"])),
            row["bed_type"].capitalize(),
            f"{int(row['beds_needed']):,}",
            f"{int(row['beds_available']):,}",
            deficit_str,
            f"{int(row['doctors_needed']):,}",
        )
    console.print(table)


def _print_icsap_risk_table(risk: pd.DataFrame):
    table = Table(title="ICSAP Risk Prediction — Top 15 At-Risk Municipalities (2025)")
    table.add_column("Municipality", style="cyan")
    table.add_column("Predicted ICSAP %", justify="right")
    table.add_column("Previous ICSAP %", justify="right")
    table.add_column("Risk Category")
    table.add_column("Beds per 1K Adm", justify="right")

    for _, row in risk.head(15).iterrows():
        cat = row.get("risk_category", "?")
        cat_str = str(cat)
        if cat == "critical":
            cat_str = f"[bold red]{cat_str}[/bold red]"
        elif cat == "high":
            cat_str = f"[yellow]{cat_str}[/yellow]"
        elif cat == "moderate":
            cat_str = f"[white]{cat_str}[/white]"

        table.add_row(
            str(row["municipality"]),
            f"{row['predicted_icsap_rate']:.1f}%",
            f"{row.get('icsap_rate_lag1', 0):.1f}%",
            cat_str,
            f"{row.get('beds_per_1k_adm', 0):.1f}",
        )
    console.print(table)


def _print_allocation_table(allocation: pd.DataFrame):
    table = Table(title="Optimal Bed Allocation (Budget: 5,000 beds)")
    table.add_column("Municipality", style="cyan")
    table.add_column("Beds Allocated", justify="right")
    table.add_column("Deficit Before", justify="right")
    table.add_column("Deficit After", justify="right")
    table.add_column("ICSAP Risk %", justify="right")
    table.add_column("Priority Score", justify="right")

    for _, row in allocation.head(20).iterrows():
        table.add_row(
            str(row["municipality"]),
            f"{int(row['beds_allocated']):,}",
            f"{int(row['deficit_before']):,}",
            f"{int(row['deficit_after']):,}",
            f"{row['icsap_risk']:.1f}%",
            f"{row['priority_score']:.0f}",
        )

    total_alloc = allocation["beds_allocated"].sum()
    console.print(table)
    console.print(f"  Total beds allocated: [bold]{int(total_alloc):,}[/bold] / 5,000")
    console.print(f"  Municipalities served: [bold]{len(allocation)}[/bold]")


def _plot_demand_projection(historical: pd.DataFrame, projections: pd.DataFrame):
    """State-level demand: historical + projected."""
    hist_state = (
        historical.groupby(["year", "month"])
        .agg(admissions=("admissions", "sum"))
        .reset_index()
    )
    hist_state["date"] = pd.to_datetime(
        hist_state["year"].astype(str) + "-" + hist_state["month"].astype(str).str.zfill(2) + "-01"
    )
    hist_state["source"] = "Historical"

    proj_state = (
        projections.groupby(["year", "month"])
        .agg(admissions=("admissions", "sum"))
        .reset_index()
    )
    proj_state["date"] = pd.to_datetime(
        proj_state["year"].astype(str) + "-" + proj_state["month"].astype(str).str.zfill(2) + "-01"
    )
    proj_state["source"] = "ML Forecast"

    fig, ax = plt.subplots(figsize=(16, 5))
    hist_sorted = hist_state.sort_values("date")
    proj_sorted = proj_state.sort_values("date")

    ax.plot(hist_sorted["date"], hist_sorted["admissions"], color="#3498db", linewidth=1.2, label="Historical")
    ax.plot(proj_sorted["date"], proj_sorted["admissions"], color="#e74c3c", linewidth=2,
            linestyle="--", label="ML Forecast (LightGBM)")
    ax.fill_between(proj_sorted["date"], proj_sorted["admissions"] * 0.85,
                    proj_sorted["admissions"] * 1.15, alpha=0.15, color="#e74c3c", label="±15% interval")

    ax.axvline(pd.Timestamp("2026-01-01"), color="#666", linestyle=":", linewidth=1)
    ax.text(pd.Timestamp("2026-02-01"), ax.get_ylim()[1] * 0.95, "Forecast →",
            fontsize=10, color="#666")

    ax.set_title("Hospital Admissions — Historical + ML Forecast (São Paulo)",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Monthly Admissions")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x / 1e3:.0f}K"))
    ax.legend(loc="upper left")

    plt.tight_layout()
    plt.savefig(PLOT_DIR / "ml_01_demand_projection.png", dpi=150, bbox_inches="tight")
    plt.close()
    console.print("  Saved ml_01_demand_projection.png")


def _plot_future_gap_evolution(future_state: pd.DataFrame):
    """Bar chart showing gap evolution 2026-2028."""
    clinical = future_state[future_state["bed_type"] == "clinical"].sort_values("year")
    if len(clinical) == 0:
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: deficit by year
    ax = axes[0]
    years = clinical["year"].values
    deficits = clinical["deficit"].values
    bars = ax.bar(years, deficits, color="#e74c3c", edgecolor="white", width=0.5)
    ax.set_title("Clinical Bed Deficit — Projection", fontsize=12, fontweight="bold")
    ax.set_ylabel("Bed Deficit")
    ax.set_xticks(years)
    for bar, val in zip(bars, deficits):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(deficits) * 0.02,
                f"{int(val):,}", ha="center", fontsize=10, fontweight="bold")

    # Right: doctors needed
    ax = axes[1]
    doctors = clinical["doctors_needed"].values
    bars = ax.bar(years, doctors, color="#3498db", edgecolor="white", width=0.5)
    ax.set_title("Additional Doctors Needed — Projection", fontsize=12, fontweight="bold")
    ax.set_ylabel("Physicians")
    ax.set_xticks(years)
    for bar, val in zip(bars, doctors):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(doctors) * 0.02,
                f"{int(val):,}", ha="center", fontsize=10, fontweight="bold")

    fig.suptitle("ML Forecast: São Paulo Clinical Bed Gap (2026-2028)",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(PLOT_DIR / "ml_02_gap_evolution.png", dpi=150, bbox_inches="tight")
    plt.close()
    console.print("  Saved ml_02_gap_evolution.png")


def _plot_icsap_risk(risk: pd.DataFrame):
    top = risk.head(20).sort_values("predicted_icsap_rate")

    fig, ax = plt.subplots(figsize=(12, 7))

    colors = {
        "critical": "#e74c3c", "high": "#e67e22", "moderate": "#f1c40f", "low": "#2ecc71"
    }
    bar_colors = [colors.get(str(c), "#999") for c in top["risk_category"]]

    bars = ax.barh(range(len(top)), top["predicted_icsap_rate"],
                   color=bar_colors, edgecolor="white", height=0.6)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top["municipality"], fontsize=9)
    ax.set_xlabel("Predicted ICSAP Rate (%)")
    ax.set_title("ML-Predicted ICSAP Risk — Top 20 Municipalities (2025)",
                 fontsize=13, fontweight="bold")
    ax.axvline(20, color="#2ecc71", linestyle="--", linewidth=1, label="Target (<20%)")
    ax.legend()

    for bar, val in zip(bars, top["predicted_icsap_rate"]):
        ax.text(val + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=9)

    plt.tight_layout()
    plt.savefig(PLOT_DIR / "ml_03_icsap_risk.png", dpi=150, bbox_inches="tight")
    plt.close()
    console.print("  Saved ml_03_icsap_risk.png")


def _plot_feature_importance(model, title: str, filename: str):
    importance = model.feature_importance(importance_type="gain")
    feature_names = model.feature_name()

    sorted_idx = np.argsort(importance)[-15:]
    top_names = [feature_names[i] for i in sorted_idx]
    top_importance = importance[sorted_idx]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(range(len(top_names)), top_importance, color="#3498db", edgecolor="white", height=0.6)
    ax.set_yticks(range(len(top_names)))
    ax.set_yticklabels(top_names, fontsize=9)
    ax.set_xlabel("Feature Importance (gain)")
    ax.set_title(f"{title} — Feature Importance", fontsize=13, fontweight="bold")

    plt.tight_layout()
    plt.savefig(PLOT_DIR / filename, dpi=150, bbox_inches="tight")
    plt.close()
    console.print(f"  Saved {filename}")


def _plot_allocation(allocation: pd.DataFrame):
    top = allocation.head(15).sort_values("beds_allocated")

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(range(len(top)), top["beds_allocated"],
                   color="#2ecc71", edgecolor="white", height=0.6)

    deficit_remaining = top["deficit_after"].values
    ax.barh(range(len(top)), deficit_remaining, left=top["beds_allocated"].values,
            color="#e74c3c", edgecolor="white", height=0.6, alpha=0.4, label="Remaining deficit")

    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top["municipality"], fontsize=9)
    ax.set_xlabel("Beds")
    ax.set_title("Optimal Bed Allocation — Top 15 Priority Municipalities",
                 fontsize=13, fontweight="bold")
    ax.legend(["Allocated", "Remaining deficit"])

    for bar, alloc, risk in zip(bars, top["beds_allocated"], top["icsap_risk"]):
        ax.text(alloc + top["deficit_after"].max() * 0.05,
                bar.get_y() + bar.get_height() / 2,
                f"{int(alloc)} beds (ICSAP: {risk:.0f}%)", va="center", fontsize=8)

    plt.tight_layout()
    plt.savefig(PLOT_DIR / "ml_06_allocation.png", dpi=150, bbox_inches="tight")
    plt.close()
    console.print("  Saved ml_06_allocation.png")


def _save_ml_metrics(future_state, risk, allocation):
    metrics = {
        "future_gap": future_state.to_dict("records"),
    }
    if len(risk) > 0:
        metrics["icsap_risk_top20"] = risk.head(20)[
            ["municipality", "predicted_icsap_rate", "icsap_rate_lag1", "risk_category"]
        ].to_dict("records")
    if len(allocation) > 0:
        metrics["allocation"] = allocation.to_dict("records")

    with open(OUTPUT_DIR / "ml_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2, default=str)


if __name__ == "__main__":
    run_ml_pipeline()

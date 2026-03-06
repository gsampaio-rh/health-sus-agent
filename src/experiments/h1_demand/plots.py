"""H1 — Hospital Bed Demand Forecasting plots."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

from src.experiments.h1_demand.data_loader import load_sih_admissions, build_monthly_demand, ESPEC_NAMES

SIH_DIR = Path("data/sih")
OUTPUT_DIR = Path("analysis/h1_demand")
PLOT_DIR = OUTPUT_DIR / "plots"

sns.set_theme(style="whitegrid", font_scale=1.1)
PALETTE = {"seasonal_naive": "#e67e22", "historical_mean": "#95a5a6", "lightgbm": "#2ecc71"}


def _load_metrics() -> list[dict]:
    with open(OUTPUT_DIR / "metrics.json") as f:
        return json.load(f)


def plot_mape_comparison():
    """Bar chart comparing MAPE across models at State and Municipality level."""
    metrics = _load_metrics()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=False)

    for i, level in enumerate(["State (SP)", "Municipality"]):
        ax = axes[i]
        level_metrics = [m for m in metrics if m["model"].startswith(level)]
        level_metrics.sort(key=lambda m: m["mape"])

        names = [m["model"].split(" | ")[1] for m in level_metrics]
        mapes = [m["mape"] for m in level_metrics]
        ci_low = [m["mape"] - m["mape_ci"][0] for m in level_metrics]
        ci_high = [m["mape_ci"][1] - m["mape"] for m in level_metrics]
        colors = [PALETTE.get(n, "#999") for n in names]

        bars = ax.barh(range(len(names)), mapes, xerr=[ci_low, ci_high],
                       color=colors, capsize=4, edgecolor="white", linewidth=0.5, height=0.5)
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=11)
        ax.set_xlabel("MAPE (%)")
        ax.set_title(f"{level} Level", fontsize=13, fontweight="bold")
        ax.axvline(15, color="#e74c3c", linestyle="--", linewidth=1, alpha=0.7, label="15% target")
        ax.legend(fontsize=9)

        for bar, val in zip(bars, mapes):
            ax.text(val + 1.5, bar.get_y() + bar.get_height() / 2,
                    f"{val:.1f}%", va="center", fontsize=10, fontweight="bold")

    fig.suptitle("H1: Hospital Demand Forecasting — MAPE by Model", fontsize=15, fontweight="bold")
    plt.tight_layout()
    plt.savefig(PLOT_DIR / "01_mape_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved 01_mape_comparison.png")


def plot_all_metrics():
    """Multi-metric comparison table as a heatmap-style figure."""
    metrics = _load_metrics()

    models = [m["model"] for m in metrics]
    metric_names = ["MAPE (%)", "MAE", "RMSE", "Within ±15%"]
    data = np.array([
        [m["mape"], m["mae"], m["rmse"], m["within_15pct"]]
        for m in metrics
    ])

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis("off")

    row_colors = []
    for m in models:
        name = m.split(" | ")[1]
        row_colors.append(PALETTE.get(name, "#ddd") + "40")

    the_table = ax.table(
        cellText=[[f"{v:.1f}" for v in row] for row in data],
        rowLabels=models,
        colLabels=metric_names,
        cellLoc="center",
        loc="center",
    )
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(10)
    the_table.scale(1.2, 1.5)

    for (row, col), cell in the_table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#2c3e50")
            cell.set_text_props(color="white", fontweight="bold")
        elif col == -1:
            cell.set_text_props(fontweight="bold", fontsize=9)

    fig.suptitle("H1: Full Metric Summary", fontsize=14, fontweight="bold", y=0.98)
    plt.savefig(PLOT_DIR / "02_metrics_table.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved 02_metrics_table.png")


def plot_monthly_admissions_time_series():
    """State-level monthly admissions per specialty (2016-2025)."""
    print("  Loading SIH data for time series...")
    sih = load_sih_admissions(SIH_DIR)
    demand = build_monthly_demand(sih)

    state_monthly = (
        demand.groupby(["year", "month", "espec"])["admissions"]
        .sum()
        .reset_index()
    )
    state_monthly["date"] = pd.to_datetime(
        state_monthly["year"].astype(str) + "-" + state_monthly["month"].astype(str).str.zfill(2) + "-01"
    )
    state_monthly["espec_name"] = state_monthly["espec"].map(ESPEC_NAMES).fillna("Outro")

    top_specs = state_monthly.groupby("espec")["admissions"].sum().nlargest(4).index
    plot_data = state_monthly[state_monthly["espec"].isin(top_specs)]

    fig, ax = plt.subplots(figsize=(16, 6))

    spec_colors = {"Clínica Médica": "#3498db", "Cirurgia": "#e74c3c", "Obstetrícia": "#2ecc71", "Pediatria": "#9b59b6"}
    for spec, group in plot_data.groupby("espec_name"):
        group = group.sort_values("date")
        color = spec_colors.get(spec, "#999")
        ax.plot(group["date"], group["admissions"], label=spec, linewidth=1.5, color=color)
        ax.fill_between(group["date"], group["admissions"], alpha=0.1, color=color)

    ax.axvspan(pd.Timestamp("2020-03-01"), pd.Timestamp("2021-06-01"),
               alpha=0.1, color="red", label="COVID-19 peak")
    ax.axvline(pd.Timestamp("2024-01-01"), color="#666", linestyle="--", linewidth=1, label="Test period start")

    ax.set_title("Monthly Hospital Admissions by Specialty — São Paulo", fontsize=14, fontweight="bold")
    ax.set_ylabel("Admissions per month")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x / 1e3:.0f}K"))
    ax.legend(loc="upper right", fontsize=9)
    ax.set_xlim(pd.Timestamp("2016-01-01"), pd.Timestamp("2025-12-31"))

    plt.tight_layout()
    plt.savefig(PLOT_DIR / "03_monthly_admissions.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved 03_monthly_admissions.png")


def plot_total_admissions_by_year():
    """Annual total admissions bar chart."""
    sih = load_sih_admissions(SIH_DIR)
    yearly = sih.groupby("year").size().reset_index(name="admissions")
    yearly = yearly[(yearly["year"] >= 2016) & (yearly["year"] <= 2025)]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(yearly["year"], yearly["admissions"], color="#3498db", edgecolor="white", width=0.7)

    for bar, val in zip(bars, yearly["admissions"]):
        label = f"{val / 1e6:.1f}M"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + yearly["admissions"].max() * 0.02,
                label, ha="center", fontsize=10, fontweight="bold")

    ax.set_title("Annual Hospital Admissions — São Paulo", fontsize=14, fontweight="bold")
    ax.set_ylabel("Admissions")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x / 1e6:.1f}M"))
    ax.set_xticks(yearly["year"])
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig(PLOT_DIR / "04_yearly_admissions.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved 04_yearly_admissions.png")


def generate_all_plots():
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating H1 plots...")
    plot_mape_comparison()
    plot_all_metrics()
    plot_monthly_admissions_time_series()
    plot_total_admissions_by_year()
    print(f"Done! Plots saved to {PLOT_DIR}/")


if __name__ == "__main__":
    generate_all_plots()

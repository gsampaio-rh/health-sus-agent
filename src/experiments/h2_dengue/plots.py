"""H2 — Dengue Epidemic Early Warning plots."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

from src.experiments.h2_dengue.data_loader import load_dengue_sp, build_weekly_series

SINAN_DIR = Path("data/sinan")
OUTPUT_DIR = Path("analysis/h2_dengue")
PLOT_DIR = OUTPUT_DIR / "plots"

sns.set_theme(style="whitegrid", font_scale=1.1)
COLORS = {"lightgbm": "#2ecc71", "xgboost": "#3498db", "seasonal_naive": "#e67e22", "majority_class": "#95a5a6"}


def plot_dengue_time_series():
    """Weekly dengue cases in SP (2017-2025) with seasonality."""
    confirmed = load_dengue_sp(SINAN_DIR)
    weekly = build_weekly_series(confirmed, min_cases_total=100)

    state_weekly = weekly.groupby(["epi_year", "epi_week"])["cases"].sum().reset_index()
    state_weekly = state_weekly.sort_values(["epi_year", "epi_week"])
    state_weekly["idx"] = range(len(state_weekly))

    fig, ax = plt.subplots(figsize=(16, 5))
    ax.fill_between(state_weekly["idx"], state_weekly["cases"], alpha=0.3, color="#e74c3c")
    ax.plot(state_weekly["idx"], state_weekly["cases"], linewidth=0.8, color="#c0392b")

    for year in range(2017, 2026):
        yr_data = state_weekly[state_weekly["epi_year"] == year]
        if len(yr_data) > 0:
            mid = yr_data["idx"].iloc[len(yr_data) // 2]
            ax.text(mid, -state_weekly["cases"].max() * 0.06, str(year),
                    ha="center", fontsize=9, color="#666")
            ax.axvline(yr_data["idx"].iloc[0], color="#ddd", linewidth=0.5, zorder=0)

    ax.set_title("Weekly Confirmed Dengue Cases — São Paulo (2017–2025)", fontsize=14, fontweight="bold")
    ax.set_ylabel("Cases per week")
    ax.set_xlabel("")
    ax.set_xticks([])
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig(PLOT_DIR / "01_dengue_time_series.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved 01_dengue_time_series.png")


def plot_yearly_cases():
    """Annual confirmed dengue cases bar chart."""
    confirmed = load_dengue_sp(SINAN_DIR)
    sem_str = confirmed["SEM_NOT"].astype(str)
    confirmed = confirmed.copy()
    confirmed["epi_year"] = sem_str.str[:4].astype(int)

    yearly = confirmed.groupby("epi_year").size().reset_index(name="cases")
    yearly = yearly[(yearly["epi_year"] >= 2017) & (yearly["epi_year"] <= 2025)]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(yearly["epi_year"], yearly["cases"], color="#e74c3c", edgecolor="white", width=0.7)

    for bar, val in zip(bars, yearly["cases"]):
        label = f"{val / 1e6:.1f}M" if val >= 1_000_000 else f"{val / 1e3:.0f}K"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + yearly["cases"].max() * 0.02,
                label, ha="center", fontsize=10, fontweight="bold")

    ax.set_title("Annual Confirmed Dengue Cases — São Paulo", fontsize=14, fontweight="bold")
    ax.set_ylabel("Cases")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x / 1e6:.1f}M"))
    ax.set_xticks(yearly["epi_year"])
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig(PLOT_DIR / "02_yearly_cases.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved 02_yearly_cases.png")


def plot_top_municipalities():
    """Top 10 municipalities by total dengue cases."""
    confirmed = load_dengue_sp(SINAN_DIR)
    weekly = build_weekly_series(confirmed, min_cases_total=100)

    muni_totals = weekly.groupby("municipality")["cases"].sum().nlargest(10).sort_values()

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(range(len(muni_totals)), muni_totals.values,
                   color="#e74c3c", edgecolor="white", height=0.6)
    ax.set_yticks(range(len(muni_totals)))
    ax.set_yticklabels(muni_totals.index, fontsize=10)
    ax.set_xlabel("Total Confirmed Cases (2017–2025)")
    ax.set_title("Top 10 Municipalities by Dengue Cases — São Paulo", fontsize=14, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x / 1e3:.0f}K"))

    for bar, val in zip(bars, muni_totals.values):
        ax.text(val + muni_totals.max() * 0.02, bar.get_y() + bar.get_height() / 2,
                f"{val / 1e3:.0f}K", va="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    plt.savefig(PLOT_DIR / "03_top_municipalities.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved 03_top_municipalities.png")


def plot_model_comparison():
    """F1 scores by model and horizon (requires metrics.json)."""
    metrics_path = OUTPUT_DIR / "metrics.json"
    if not metrics_path.exists():
        print("  [SKIP] 04_f1_comparison.png — metrics.json not found (re-run experiment first)")
        return

    metrics = json.load(open(metrics_path))

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

    for i, horizon in enumerate([4, 8]):
        ax = axes[i]
        h_metrics = [m for m in metrics if m["horizon"] == horizon]
        h_metrics.sort(key=lambda m: m["f1"], reverse=True)

        names = [m["model"] for m in h_metrics]
        f1s = [m["f1"] for m in h_metrics]
        ci_low = [m["f1"] - m["f1_ci"][0] for m in h_metrics]
        ci_high = [m["f1_ci"][1] - m["f1"] for m in h_metrics]
        colors = [COLORS.get(n, "#999") for n in names]

        bars = ax.barh(range(len(names)), f1s, xerr=[ci_low, ci_high],
                       color=colors, capsize=4, edgecolor="white", linewidth=0.5)
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names)
        ax.set_xlabel("F1 Score")
        ax.set_title(f"{horizon}-Week Horizon", fontsize=12, fontweight="bold")
        ax.axvline(0.7, color="#e74c3c", linestyle="--", linewidth=1, label="Target (0.70)")
        ax.set_xlim(0, 1)
        ax.legend(fontsize=9)

        for bar, val in zip(bars, f1s):
            ax.text(val + 0.02, bar.get_y() + bar.get_height() / 2,
                    f"{val:.3f}", va="center", fontsize=10)

    fig.suptitle("H2: Dengue Epidemic Classification — F1 by Model", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(PLOT_DIR / "04_f1_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved 04_f1_comparison.png")


def plot_precision_recall():
    """Precision vs Recall scatter (requires metrics.json)."""
    metrics_path = OUTPUT_DIR / "metrics.json"
    if not metrics_path.exists():
        print("  [SKIP] 05_precision_recall.png — metrics.json not found")
        return

    metrics = json.load(open(metrics_path))

    fig, ax = plt.subplots(figsize=(8, 6))

    markers = {4: "o", 8: "s"}
    for m in metrics:
        color = COLORS.get(m["model"], "#999")
        marker = markers.get(m["horizon"], "o")
        label = f"{m['model']} ({m['horizon']}w)"
        ax.scatter(m["recall"], m["precision"], s=120, color=color, marker=marker,
                   edgecolors="white", linewidth=1, label=label, zorder=5)
        ax.annotate(f"F1={m['f1']:.2f}", (m["recall"] + 0.01, m["precision"] + 0.01), fontsize=8)

    for f1_val in [0.3, 0.5, 0.7, 0.9]:
        r = np.linspace(0.01, 1, 100)
        p = (f1_val * r) / (2 * r - f1_val)
        valid = (p > 0) & (p <= 1)
        ax.plot(r[valid], p[valid], "--", color="#ddd", linewidth=0.8)
        idx = np.argmin(np.abs(r - 0.95))
        if valid[idx]:
            ax.text(r[idx], p[idx], f"F1={f1_val}", fontsize=7, color="#aaa")

    ax.set_xlabel("Recall", fontsize=12)
    ax.set_ylabel("Precision", fontsize=12)
    ax.set_title("H2: Precision vs Recall — All Models", fontsize=14, fontweight="bold")
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=8, loc="lower left")

    plt.tight_layout()
    plt.savefig(PLOT_DIR / "05_precision_recall.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved 05_precision_recall.png")


def generate_all_plots():
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating H2 plots...")
    plot_dengue_time_series()
    plot_yearly_cases()
    plot_top_municipalities()
    plot_model_comparison()
    plot_precision_recall()
    print(f"Done! Plots saved to {PLOT_DIR}/")


if __name__ == "__main__":
    generate_all_plots()

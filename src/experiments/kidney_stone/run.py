"""Run the kidney stone epidemic deep investigation.

Usage:
    python -m src.experiments.kidney_stone.run
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from loguru import logger

from src.experiments.kidney_stone.investigate import (
    load_kidney_stone_data,
    analyze_yearly_trend,
    analyze_seasonality,
    analyze_seasonality_by_year,
    analyze_sex_distribution,
    analyze_age_distribution,
    analyze_municipality_hotspots,
    analyze_subdiagnosis,
    analyze_urban_vs_interior,
    analyze_severity_over_time,
    SP_MUNICIPALITIES,
    OUTPUT_DIR,
)

PLOT_DIR = OUTPUT_DIR / "plots"


def _save(fig, name: str):
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    path = PLOT_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"  Saved {path}")


def plot_yearly_trend(yearly: pd.DataFrame):
    fig, ax1 = plt.subplots(figsize=(12, 6))

    color_bar = "#2196F3"
    color_line = "#F44336"

    ax1.bar(yearly["year"], yearly["admissions"], color=color_bar, alpha=0.7, label="Admissions")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Admissions", color=color_bar)
    ax1.tick_params(axis="y", labelcolor=color_bar)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    ax2 = ax1.twinx()
    ax2.plot(yearly["year"], yearly["avg_stay"], color=color_line, marker="o", linewidth=2, label="Avg Stay (days)")
    ax2.set_ylabel("Avg Length of Stay (days)", color=color_line)
    ax2.tick_params(axis="y", labelcolor=color_line)

    ax1.set_title("Kidney Stone (N20) Admissions — São Paulo State", fontsize=14, fontweight="bold")
    ax1.set_xticks(yearly["year"])

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    for _, row in yearly.iterrows():
        ax1.text(row["year"], row["admissions"] + 200, f"{row['admissions']:,.0f}",
                 ha="center", va="bottom", fontsize=7, rotation=45)

    fig.tight_layout()
    _save(fig, "01_yearly_trend.png")


def plot_seasonality(avg_monthly: pd.DataFrame, by_year: pd.DataFrame):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    season_colors = {
        "Summer": "#FF5722",
        "Autumn": "#FF9800",
        "Winter": "#2196F3",
        "Spring": "#4CAF50",
    }
    colors = [season_colors[s] for s in avg_monthly["season"]]

    ax1.bar(avg_monthly["month_name"], avg_monthly["avg_admissions"], color=colors)
    ax1.set_title("Average Monthly Admissions (all years)", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Avg Admissions")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=c, label=s) for s, c in season_colors.items()]
    ax1.legend(handles=legend_elements, loc="upper right")

    for year in sorted(by_year["year"].unique()):
        subset = by_year[by_year["year"] == year]
        ax2.plot(subset["month"], subset["admissions"], marker=".", alpha=0.6, label=str(year))

    ax2.set_title("Monthly Admissions by Year", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Month")
    ax2.set_ylabel("Admissions")
    ax2.set_xticks(range(1, 13))
    ax2.legend(fontsize=7, ncol=2)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    fig.suptitle("Seasonality — Is Summer = More Kidney Stones?", fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    _save(fig, "02_seasonality.png")


def plot_sex_distribution(sex_df: pd.DataFrame):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    sex_colors = {"Male": "#2196F3", "Female": "#E91E63", "Other/Unknown": "#9E9E9E"}

    for sex in ["Male", "Female"]:
        subset = sex_df[sex_df["sex"] == sex]
        ax1.plot(subset["year"], subset["admissions"], marker="o", linewidth=2,
                 color=sex_colors[sex], label=sex)
        ax1.fill_between(subset["year"], 0, subset["admissions"], alpha=0.1, color=sex_colors[sex])

    ax1.set_title("Admissions by Sex", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Admissions")
    ax1.legend()
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    for sex in ["Male", "Female"]:
        subset = sex_df[sex_df["sex"] == sex]
        ax2.plot(subset["year"], subset["share_pct"], marker="o", linewidth=2,
                 color=sex_colors[sex], label=f"{sex} %")

    ax2.set_title("Sex Distribution Over Time (%)", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Share (%)")
    ax2.set_ylim(0, 100)
    ax2.legend()

    fig.suptitle("Kidney Stones by Sex — Who Is Getting Hit?", fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    _save(fig, "03_sex_distribution.png")


def plot_age_distribution(age_df: pd.DataFrame):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    age_order = ["0-17", "18-29", "30-39", "40-49", "50-59", "60-69", "70+"]
    age_colors = plt.cm.viridis(np.linspace(0.15, 0.85, len(age_order)))

    early = age_df[age_df["year"] == age_df["year"].min()]
    late = age_df[age_df["year"] == age_df["year"].max()]

    early_ordered = early.set_index("age_group").reindex(age_order).fillna(0)
    late_ordered = late.set_index("age_group").reindex(age_order).fillna(0)

    x = np.arange(len(age_order))
    width = 0.35

    ax1.bar(x - width / 2, early_ordered["admissions"], width, label=f"{int(age_df['year'].min())}",
            color="#90CAF9")
    ax1.bar(x + width / 2, late_ordered["admissions"], width, label=f"{int(age_df['year'].max())}",
            color="#1565C0")
    ax1.set_xticks(x)
    ax1.set_xticklabels(age_order)
    ax1.set_title(f"Age Distribution: {int(age_df['year'].min())} vs {int(age_df['year'].max())}",
                  fontsize=12, fontweight="bold")
    ax1.set_ylabel("Admissions")
    ax1.legend()
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    for idx, ag in enumerate(age_order):
        subset = age_df[age_df["age_group"] == ag]
        ax2.plot(subset["year"], subset["admissions"], marker=".", linewidth=2,
                 color=age_colors[idx], label=ag)

    ax2.set_title("Age Group Trends Over Time", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Admissions")
    ax2.legend(fontsize=8)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    fig.suptitle("Age Analysis — Which Age Groups Are Driving the Epidemic?",
                 fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    _save(fig, "04_age_distribution.png")


def plot_municipality_hotspots(hotspots: pd.DataFrame):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    top20_volume = hotspots.head(20).copy()
    top20_volume["label"] = top20_volume["muni_name"].apply(lambda x: x[:20])

    ax1.barh(range(len(top20_volume)), top20_volume["late_admissions"],
             color="#1565C0", alpha=0.8, label="2022-2024")
    ax1.barh(range(len(top20_volume)), -top20_volume["early_admissions"],
             color="#90CAF9", alpha=0.8, label="2016-2018")
    ax1.set_yticks(range(len(top20_volume)))
    ax1.set_yticklabels(top20_volume["label"], fontsize=8)
    ax1.set_title("Top 20 Municipalities by Volume", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Admissions (left=early, right=late)")
    ax1.legend(fontsize=8)
    ax1.invert_yaxis()

    growing = hotspots[
        (hotspots["early_admissions"] >= 50) & (hotspots["growth_pct"].notna())
    ].sort_values("growth_pct", ascending=False).head(20).copy()
    growing["label"] = growing["muni_name"].apply(lambda x: x[:20])
    colors = ["#F44336" if g > 100 else "#FF9800" if g > 50 else "#4CAF50" for g in growing["growth_pct"]]

    ax2.barh(range(len(growing)), growing["growth_pct"], color=colors, alpha=0.8)
    ax2.set_yticks(range(len(growing)))
    ax2.set_yticklabels(growing["label"], fontsize=8)
    ax2.set_title("Top 20 Fastest-Growing (min 50 early cases)", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Growth %")
    ax2.invert_yaxis()

    for i, v in enumerate(growing["growth_pct"]):
        ax2.text(v + 2, i, f"{v:.0f}%", va="center", fontsize=7)

    fig.suptitle("WHERE — Geographic Hotspots", fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    _save(fig, "05_municipality_hotspots.png")


def plot_urban_vs_interior(region_df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 6))

    for region, color in [("SP Metro", "#1565C0"), ("Interior", "#4CAF50")]:
        subset = region_df[region_df["region"] == region]
        ax.plot(subset["year"], subset["admissions"], marker="o", linewidth=2.5,
                color=color, label=region)
        ax.fill_between(subset["year"], 0, subset["admissions"], alpha=0.1, color=color)

    ax.set_title("Kidney Stones: SP Metropolitan Area vs Interior",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Admissions")
    ax.set_xlabel("Year")
    ax.legend()
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    fig.tight_layout()
    _save(fig, "06_urban_vs_interior.png")


def plot_subdiagnosis(sub_df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(12, 6))

    sub_colors = {
        "Kidney calculus": "#1565C0",
        "Ureteral calculus": "#F44336",
        "Kidney + ureteral": "#FF9800",
        "Urinary calculus NOS": "#9E9E9E",
    }

    for label in sub_df["label"].unique():
        subset = sub_df[sub_df["label"] == label]
        color = sub_colors.get(label, "#666666")
        ax.plot(subset["year"], subset["admissions"], marker="o", linewidth=2,
                color=color, label=label)

    ax.set_title("Which Type of Stone Is Driving the Epidemic?",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Admissions")
    ax.set_xlabel("Year")
    ax.legend()
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    fig.tight_layout()
    _save(fig, "07_subdiagnosis.png")


def plot_severity(severity: pd.DataFrame):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    axes[0, 0].plot(severity["year"], severity["avg_stay"], marker="o", color="#1565C0", linewidth=2)
    axes[0, 0].set_title("Avg Length of Stay (days)")
    axes[0, 0].set_ylabel("Days")

    axes[0, 1].plot(severity["year"], severity["mortality_per_10k"], marker="o", color="#F44336", linewidth=2)
    axes[0, 1].set_title("Mortality Rate (per 10,000 admissions)")
    axes[0, 1].set_ylabel("Deaths per 10K")

    axes[1, 0].plot(severity["year"], severity["avg_cost"], marker="o", color="#4CAF50", linewidth=2)
    axes[1, 0].set_title("Avg Cost per Admission (R$)")
    axes[1, 0].set_ylabel("R$")
    axes[1, 0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R${x:,.0f}"))

    axes[1, 1].plot(severity["year"], severity["pct_over_5_days"], marker="o", color="#FF9800", linewidth=2)
    axes[1, 1].set_title("% Admissions > 5 Days Stay")
    axes[1, 1].set_ylabel("%")

    for ax in axes.flat:
        ax.set_xlabel("Year")
        ax.grid(alpha=0.3)

    fig.suptitle("Severity Trends — Are Kidney Stones Getting Worse?",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    _save(fig, "08_severity_trends.png")


def print_summary_table(yearly: pd.DataFrame):
    print("\n" + "=" * 90)
    print("  KIDNEY STONE (N20) — YEARLY TREND")
    print("=" * 90)
    print(f"  {'Year':>6}  {'Admissions':>12}  {'Avg Stay':>10}  {'Deaths':>8}  {'Mort/10K':>10}  {'Avg Cost':>10}")
    print("-" * 90)
    for _, r in yearly.iterrows():
        print(f"  {int(r['year']):>6}  {r['admissions']:>12,.0f}  {r['avg_stay']:>10.1f}  "
              f"{r['deaths']:>8,.0f}  {r['mortality_per_1000']*10:>10.1f}  R${r['avg_cost']:>9,.0f}")
    print()

    first = yearly.iloc[0]
    last = yearly.iloc[-1]
    growth = (last["admissions"] - first["admissions"]) / first["admissions"] * 100
    print(f"  Total growth: {growth:+.1f}% ({int(first['year'])} → {int(last['year'])})")
    print(f"  {int(first['year'])}: {first['admissions']:,.0f} → {int(last['year'])}: {last['admissions']:,.0f}")
    print()


def print_seasonality_summary(avg_monthly: pd.DataFrame):
    print("\n" + "=" * 60)
    print("  SEASONALITY ANALYSIS")
    print("=" * 60)

    season_avg = avg_monthly.groupby("season")["avg_admissions"].mean()
    for season in ["Summer", "Autumn", "Winter", "Spring"]:
        val = season_avg.get(season, 0)
        print(f"  {season:>8}: {val:,.0f} avg monthly admissions")

    summer = season_avg.get("Summer", 0)
    winter = season_avg.get("Winter", 0)
    diff_pct = (summer - winter) / winter * 100 if winter > 0 else 0
    print(f"\n  Summer vs Winter difference: {diff_pct:+.1f}%")
    print()


def print_hotspot_summary(hotspots: pd.DataFrame):
    print("\n" + "=" * 90)
    print("  TOP 15 MUNICIPALITY HOTSPOTS (by 2022-2024 volume)")
    print("=" * 90)
    print(f"  {'Municipality':<25} {'2016-18':>10} {'2022-24':>10} {'Growth':>10}")
    print("-" * 90)
    for _, r in hotspots.head(15).iterrows():
        name = r["muni_name"][:24]
        growth = f"{r['growth_pct']:+.0f}%" if pd.notna(r["growth_pct"]) else "NEW"
        print(f"  {name:<25} {r['early_admissions']:>10,.0f} {r['late_admissions']:>10,.0f} {growth:>10}")
    print()


def main():
    logger.info("Loading kidney stone (N20) data...")
    df = load_kidney_stone_data()

    logger.info("Analyzing yearly trend...")
    yearly = analyze_yearly_trend(df)
    print_summary_table(yearly)

    logger.info("Analyzing seasonality...")
    avg_monthly = analyze_seasonality(df)
    by_year = analyze_seasonality_by_year(df)
    print_seasonality_summary(avg_monthly)

    logger.info("Analyzing sex distribution...")
    sex_df = analyze_sex_distribution(df)

    logger.info("Analyzing age distribution...")
    age_df = analyze_age_distribution(df)

    logger.info("Analyzing municipality hotspots...")
    hotspots = analyze_municipality_hotspots(df)
    print_hotspot_summary(hotspots)

    logger.info("Analyzing urban vs interior...")
    region_df = analyze_urban_vs_interior(df)

    logger.info("Analyzing sub-diagnoses...")
    sub_df = analyze_subdiagnosis(df)

    logger.info("Analyzing severity trends...")
    severity = analyze_severity_over_time(df)

    # ── Plots ──
    logger.info("Generating plots...")
    plot_yearly_trend(yearly)
    plot_seasonality(avg_monthly, by_year)
    plot_sex_distribution(sex_df)
    plot_age_distribution(age_df)
    plot_municipality_hotspots(hotspots)
    plot_urban_vs_interior(region_df)
    plot_subdiagnosis(sub_df)
    plot_severity(severity)

    # ── Save metrics ──
    metrics = {
        "total_admissions": int(df.shape[0]),
        "years_covered": sorted(df["year"].unique().tolist()),
        "growth_pct": float(
            (yearly.iloc[-1]["admissions"] - yearly.iloc[0]["admissions"])
            / yearly.iloc[0]["admissions"] * 100
        ),
        "yearly_trend": yearly.to_dict(orient="records"),
        "seasonality": avg_monthly.to_dict(orient="records"),
        "sex_summary": sex_df.to_dict(orient="records"),
        "severity": severity.to_dict(orient="records"),
        "top_municipalities": hotspots.head(20).to_dict(orient="records"),
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    logger.info(f"Saved metrics to {OUTPUT_DIR / 'metrics.json'}")

    print("\n" + "=" * 60)
    print("  INVESTIGATION COMPLETE")
    print(f"  Plots: {PLOT_DIR}")
    print(f"  Metrics: {OUTPUT_DIR / 'metrics.json'}")
    print("=" * 60)


if __name__ == "__main__":
    main()

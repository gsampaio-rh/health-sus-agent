"""Raio-X do SUS São Paulo — main experiment runner.

Executes A1 (Avoidable Hospitalizations) and A7 (Demand-Supply Forecasting)
and generates findings + plots.

Optimized for M1 MacBook — chunk-based processing, ~4-6GB peak RAM.
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

from src.experiments.raio_x.a1_avoidable import (
    load_and_classify,
    muni_year_summary,
    summary_by_group,
    summary_state_trend,
    top_worst_municipalities,
)
from src.experiments.raio_x.a7_demand_supply import (
    calculate_beds_needed,
    calculate_gap,
    calculate_occupancy,
    estimate_doctors_needed,
    load_cnes_supply,
    load_sih_demand,
    state_level_summary,
)

OUTPUT_DIR = Path("analysis/raio_x")
PLOT_DIR = OUTPUT_DIR / "plots"

console = Console()
sns.set_theme(style="whitegrid", font_scale=1.1)


def run_a1():
    """A1: Avoidable Hospitalizations (ICSAP)."""
    console.print("\n[bold cyan]═══ A1: Internações Evitáveis (ICSAP) ═══[/bold cyan]\n")

    muni_agg, group_agg = load_and_classify()

    # State trend
    console.print("[bold]State-level ICSAP trend:[/bold]")
    trend = summary_state_trend(muni_agg)

    table = Table(title="ICSAP Rate — São Paulo State")
    table.add_column("Year", style="cyan")
    table.add_column("Total Admissions", justify="right")
    table.add_column("ICSAP Admissions", justify="right")
    table.add_column("ICSAP %", justify="right")
    table.add_column("ICSAP Cost (R$)", justify="right")

    for _, row in trend.iterrows():
        pct = row["icsap_rate_pct"]
        pct_str = f"{pct:.1f}%"
        if pct > 25:
            pct_str = f"[bold red]{pct_str}[/bold red]"
        elif pct > 20:
            pct_str = f"[yellow]{pct_str}[/yellow]"

        cost_str = f"R$ {row.get('icsap_cost', 0) / 1e6:,.1f}M"
        table.add_row(
            str(int(row["year"])),
            f"{int(row['total_admissions']):,}",
            f"{int(row['icsap_admissions']):,}",
            pct_str,
            cost_str,
        )

    console.print(table)

    # Top ICSAP groups
    console.print("\n[bold]Top ICSAP groups by volume:[/bold]")
    groups = summary_by_group(group_agg)

    group_table = Table(title="ICSAP Groups — All Years (2016–2025)")
    group_table.add_column("Condition", style="cyan")
    group_table.add_column("Admissions", justify="right")
    group_table.add_column("Avg Cost (R$)", justify="right")
    group_table.add_column("Avg Stay (days)", justify="right")
    group_table.add_column("Mortality %", justify="right")

    for _, row in groups.head(10).iterrows():
        mort_str = f"{row['mortality_rate_pct']:.1f}%"
        if row["mortality_rate_pct"] > 10:
            mort_str = f"[bold red]{mort_str}[/bold red]"
        group_table.add_row(
            row["group_name"],
            f"{int(row['admissions']):,}",
            f"R$ {row['avg_cost']:,.0f}",
            f"{row['avg_stay']:.1f}",
            mort_str,
        )

    console.print(group_table)

    # Top worst municipalities (2024)
    console.print("\n[bold]Worst municipalities by ICSAP rate (2024):[/bold]")
    muni_yr = muni_year_summary(muni_agg)
    worst = top_worst_municipalities(muni_yr, year=2024, min_admissions=2000)

    worst_table = Table(title="Top 15 Municipalities — Highest ICSAP Rate (2024)")
    worst_table.add_column("Municipality", style="cyan")
    worst_table.add_column("Total Admissions", justify="right")
    worst_table.add_column("ICSAP", justify="right")
    worst_table.add_column("ICSAP %", justify="right")

    for _, row in worst.head(15).iterrows():
        worst_table.add_row(
            row["municipality"],
            f"{int(row['total_admissions']):,}",
            f"{int(row['icsap_admissions']):,}",
            f"[bold red]{row['icsap_rate_pct']:.1f}%[/bold red]",
        )
    console.print(worst_table)

    # Total cost headline
    total_icsap_cost = trend["icsap_cost"].sum()
    console.print(f"\n[bold]Total ICSAP cost (2016-2025):[/bold] R$ {total_icsap_cost:,.0f}")
    console.print(
        f"[bold yellow]That's R$ {total_icsap_cost / 1e9:.1f} billion spent on hospitalizations "
        f"that proper primary care would have prevented.[/bold yellow]"
    )

    # Plots
    _plot_a1_trend(trend)
    _plot_a1_groups(groups)
    _plot_a1_worst_municipalities(worst)

    _save_a1_metrics(trend, groups, worst, total_icsap_cost)

    return muni_agg


def _plot_a1_trend(trend: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(trend["year"], trend["icsap_admissions"] / 1e3, color="#e74c3c", edgecolor="white",
           width=0.7, label="ICSAP admissions")

    ax2 = ax.twinx()
    ax2.plot(trend["year"], trend["icsap_rate_pct"], "o-", color="#2c3e50", linewidth=2,
             markersize=8, label="ICSAP rate (%)")
    ax2.set_ylabel("ICSAP Rate (%)", color="#2c3e50")

    ax.set_title("Internações Evitáveis (ICSAP) — Estado de São Paulo", fontsize=14, fontweight="bold")
    ax.set_ylabel("ICSAP Admissions (thousands)")
    ax.set_xticks(trend["year"].astype(int))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}K"))

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    plt.tight_layout()
    plt.savefig(PLOT_DIR / "a1_01_icsap_trend.png", dpi=150, bbox_inches="tight")
    plt.close()
    console.print("  Saved a1_01_icsap_trend.png")


def _plot_a1_groups(groups: pd.DataFrame):
    top = groups.head(10).sort_values("admissions")

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(range(len(top)), top["admissions"] / 1e3,
                   color="#e74c3c", edgecolor="white", height=0.6)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top["group_name"], fontsize=10)
    ax.set_xlabel("Admissions (thousands)")
    ax.set_title("Top 10 Condições Evitáveis (ICSAP) — São Paulo 2016–2025",
                 fontsize=14, fontweight="bold")

    for bar, val in zip(bars, top["admissions"]):
        ax.text(val / 1e3 + top["admissions"].max() / 1e3 * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{val / 1e3:.0f}K", va="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    plt.savefig(PLOT_DIR / "a1_02_icsap_groups.png", dpi=150, bbox_inches="tight")
    plt.close()
    console.print("  Saved a1_02_icsap_groups.png")


def _plot_a1_worst_municipalities(worst: pd.DataFrame):
    top = worst.head(15).sort_values("icsap_rate_pct")

    fig, ax = plt.subplots(figsize=(12, 6))

    colors = ["#e74c3c" if r > 30 else "#e67e22" if r > 25 else "#f39c12"
              for r in top["icsap_rate_pct"]]
    bars = ax.barh(range(len(top)), top["icsap_rate_pct"],
                   color=colors, edgecolor="white", height=0.6)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top["municipality"], fontsize=9)
    ax.set_xlabel("ICSAP Rate (%)")
    ax.set_title("Top 15 Municípios — Maior Taxa de Internação Evitável (2024)",
                 fontsize=13, fontweight="bold")
    ax.axvline(20, color="#2ecc71", linestyle="--", linewidth=1, label="Meta (<20%)")
    ax.legend()

    for bar, val in zip(bars, top["icsap_rate_pct"]):
        ax.text(val + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    plt.savefig(PLOT_DIR / "a1_03_worst_municipalities.png", dpi=150, bbox_inches="tight")
    plt.close()
    console.print("  Saved a1_03_worst_municipalities.png")


def _save_a1_metrics(trend, groups, worst, total_cost):
    metrics = {
        "total_icsap_cost_brl": float(total_cost),
        "trend": trend.to_dict("records"),
        "top_groups": groups.head(10).to_dict("records"),
        "worst_municipalities_2024": worst.head(20).to_dict("records"),
    }
    with open(OUTPUT_DIR / "a1_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2, default=str)


def run_a7():
    """A7: Demand-Supply Forecasting."""
    console.print("\n[bold cyan]═══ A7: Quantos Leitos e Médicos São Necessários ═══[/bold cyan]\n")

    console.print("[bold]Step 1:[/bold] Loading SIH demand...")
    demand = load_sih_demand()

    console.print("[bold]Step 2:[/bold] Loading CNES supply...")
    supply = load_cnes_supply()

    console.print("[bold]Step 3:[/bold] Calculating occupancy...")
    occupancy = calculate_occupancy(demand, supply)

    console.print("[bold]Step 4:[/bold] Calculating beds needed...")
    beds_needed = calculate_beds_needed(demand)

    console.print("[bold]Step 5:[/bold] Calculating gap...")
    gap = calculate_gap(beds_needed, supply)
    gap = estimate_doctors_needed(gap)

    # State-level summary
    state = state_level_summary(gap)

    state_table = Table(title="Déficit/Superávit de Leitos — São Paulo (meta: 85% ocupação)")
    state_table.add_column("Tipo de Leito", style="cyan")
    state_table.add_column("Necessários", justify="right")
    state_table.add_column("Disponíveis", justify="right")
    state_table.add_column("Déficit", justify="right")
    state_table.add_column("Municípios em Déficit", justify="right")
    state_table.add_column("Médicos Adicionais", justify="right")

    for _, row in state.iterrows():
        deficit = int(row["total_deficit"])
        deficit_str = f"{deficit:,}"
        if deficit > 0:
            deficit_str = f"[bold red]+{deficit_str}[/bold red]"
        state_table.add_row(
            row["bed_type"].capitalize(),
            f"{int(row['total_beds_needed']):,}",
            f"{int(row['total_beds_available']):,}",
            deficit_str,
            f"{int(row['municipalities_in_deficit']):,}",
            f"{int(row['additional_doctors']):,}",
        )

    console.print(state_table)

    # Top municipalities in deficit
    console.print("\n[bold]Top 15 municipalities with largest bed deficit:[/bold]")
    muni_deficit = (
        gap[gap["bed_deficit"] > 0]
        .groupby("municipality")
        .agg(
            total_deficit=("bed_deficit", "sum"),
            beds_needed=("beds_needed", "sum"),
            beds_available=("beds_available", "sum"),
            doctors_needed=("additional_doctors", "sum"),
        )
        .reset_index()
        .sort_values("total_deficit", ascending=False)
    )

    deficit_table = Table(title="Top 15 Municípios — Maior Déficit de Leitos")
    deficit_table.add_column("Município", style="cyan")
    deficit_table.add_column("Necessários", justify="right")
    deficit_table.add_column("Disponíveis", justify="right")
    deficit_table.add_column("Déficit", justify="right")
    deficit_table.add_column("Médicos", justify="right")

    for _, row in muni_deficit.head(15).iterrows():
        deficit_table.add_row(
            row["municipality"],
            f"{int(row['beds_needed']):,}",
            f"{int(row['beds_available']):,}",
            f"[bold red]{int(row['total_deficit']):,}[/bold red]",
            f"{int(row['doctors_needed']):,}",
        )
    console.print(deficit_table)

    # Occupancy over time (state level)
    state_occupancy = (
        occupancy.groupby(["year", "month", "bed_type"])
        .agg(
            total_bed_days=("total_bed_days", "sum"),
            total_capacity=("capacity_bed_days", "sum"),
        )
        .reset_index()
    )
    state_occupancy["occupancy_pct"] = (
        state_occupancy["total_bed_days"] / state_occupancy["total_capacity"].clip(lower=1) * 100
    )

    # Plots
    _plot_a7_occupancy(state_occupancy)
    _plot_a7_deficit_by_type(state)
    _plot_a7_top_deficit_municipalities(muni_deficit)

    _save_a7_metrics(state, muni_deficit)

    return gap


def _plot_a7_occupancy(state_occ: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(16, 5))

    bed_colors = {"surgical": "#e74c3c", "clinical": "#3498db", "obstetric": "#2ecc71"}

    for bed_type, group in state_occ.groupby("bed_type"):
        if bed_type not in bed_colors:
            continue
        group = group.copy()
        group["date"] = pd.to_datetime(
            group["year"].astype(str) + "-" + group["month"].astype(str).str.zfill(2) + "-01"
        )
        group = group.sort_values("date")
        ax.plot(group["date"], group["occupancy_pct"], label=bed_type.capitalize(),
                color=bed_colors[bed_type], linewidth=1.5)

    ax.axhline(85, color="#e67e22", linestyle="--", linewidth=1.5, label="WHO target (85%)")
    ax.axhline(100, color="#c0392b", linestyle=":", linewidth=1, alpha=0.5, label="Full capacity")

    ax.set_title("Taxa de Ocupação de Leitos Hospitalares — São Paulo",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Occupancy Rate (%)")
    ax.legend(loc="upper right")
    ax.set_ylim(0, 150)

    plt.tight_layout()
    plt.savefig(PLOT_DIR / "a7_01_occupancy_trend.png", dpi=150, bbox_inches="tight")
    plt.close()
    console.print("  Saved a7_01_occupancy_trend.png")


def _plot_a7_deficit_by_type(state: pd.DataFrame):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    bed_types = state["bed_type"].tolist()
    needed = state["total_beds_needed"].values
    available = state["total_beds_available"].values

    x = np.arange(len(bed_types))
    width = 0.35
    ax.bar(x - width / 2, needed, width, label="Necessários", color="#e74c3c", edgecolor="white")
    ax.bar(x + width / 2, available, width, label="Disponíveis", color="#2ecc71", edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels([t.capitalize() for t in bed_types])
    ax.set_ylabel("Leitos")
    ax.set_title("Leitos: Necessários vs Disponíveis", fontsize=12, fontweight="bold")
    ax.legend()
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v / 1e3:.0f}K"))

    ax = axes[1]
    doctors = state["additional_doctors"].values
    bars = ax.bar(x, doctors, color="#3498db", edgecolor="white", width=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels([t.capitalize() for t in bed_types])
    ax.set_ylabel("Médicos Adicionais")
    ax.set_title("Estimativa de Médicos Necessários", fontsize=12, fontweight="bold")

    for bar, val in zip(bars, doctors):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(doctors) * 0.02,
                    f"{int(val):,}", ha="center", fontsize=10, fontweight="bold")

    fig.suptitle("A7: Gap Demanda–Oferta — Estado de São Paulo", fontsize=15, fontweight="bold")
    plt.tight_layout()
    plt.savefig(PLOT_DIR / "a7_02_gap_by_type.png", dpi=150, bbox_inches="tight")
    plt.close()
    console.print("  Saved a7_02_gap_by_type.png")


def _plot_a7_top_deficit_municipalities(muni_deficit: pd.DataFrame):
    top = muni_deficit.head(15).sort_values("total_deficit")

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(range(len(top)), top["total_deficit"],
                   color="#e74c3c", edgecolor="white", height=0.6)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top["municipality"], fontsize=9)
    ax.set_xlabel("Déficit de Leitos (necessários − disponíveis)")
    ax.set_title("Top 15 Municípios — Maior Déficit de Leitos",
                 fontsize=13, fontweight="bold")

    for bar, val in zip(bars, top["total_deficit"]):
        ax.text(val + top["total_deficit"].max() * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{int(val):,}", va="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    plt.savefig(PLOT_DIR / "a7_03_top_deficit.png", dpi=150, bbox_inches="tight")
    plt.close()
    console.print("  Saved a7_03_top_deficit.png")


def _save_a7_metrics(state, muni_deficit):
    metrics = {
        "state_summary": state.to_dict("records"),
        "top_deficit_municipalities": muni_deficit.head(20).to_dict("records"),
    }
    with open(OUTPUT_DIR / "a7_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2, default=str)


def run_all():
    PLOT_DIR.mkdir(parents=True, exist_ok=True)

    run_a1()
    console.print()
    run_a7()

    console.print(f"\n[green]All results saved to {OUTPUT_DIR}/[/green]")


if __name__ == "__main__":
    run_all()

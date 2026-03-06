"""A7 — Demand-Supply Forecasting: How many beds and doctors are needed.

Combines SIH demand data with CNES supply data to calculate current gaps and
project future needs per municipality and specialty.
"""

from pathlib import Path

import pandas as pd
import numpy as np
from loguru import logger

SIH_DIR = Path("data/sih")
CNES_DIR = Path("data/cnes")

TARGET_OCCUPANCY = 0.85  # WHO recommended max occupancy
DAYS_PER_MONTH = 30

# MS recommended physicians per bed (approximate for SUS general hospitals)
PHYSICIANS_PER_BED = {
    "surgical": 1.5,     # surgeons + anesthesiologists
    "clinical": 1.0,     # internists
    "obstetric": 1.2,    # obstetricians + neonatologists
}

ESPEC_TO_BED_TYPE = {
    "01": "surgical",
    "02": "obstetric",
    "03": "clinical",
    "05": "clinical",    # psychiatric → clinical beds
    "07": "clinical",    # pediatric → clinical beds
}

SIH_COLS = ["ANO_CMPT", "MES_CMPT", "ESPEC", "MUNIC_MOV", "DIAS_PERM", "CNES"]


def load_sih_demand(sih_dir: Path = SIH_DIR) -> pd.DataFrame:
    """Load SIH and aggregate monthly demand: admissions and bed-days."""
    sih_files = sorted(sih_dir.glob("*.parquet"))
    dfs = [pd.read_parquet(f, columns=SIH_COLS) for f in sih_files]
    sih = pd.concat(dfs, ignore_index=True)
    logger.info(f"Loaded {len(sih):,} SIH admissions")

    sih["year"] = sih["ANO_CMPT"].astype(int)
    sih["month"] = sih["MES_CMPT"].astype(int)
    sih["municipality"] = sih["MUNIC_MOV"].astype(str).str.strip()
    sih["espec"] = sih["ESPEC"].astype(str).str.strip()
    sih["dias_perm"] = pd.to_numeric(sih["DIAS_PERM"], errors="coerce").fillna(0).astype(int)
    sih["bed_type"] = sih["espec"].map(ESPEC_TO_BED_TYPE).fillna("other")

    demand = (
        sih.groupby(["municipality", "year", "month", "bed_type"])
        .agg(
            admissions=("CNES", "count"),
            total_bed_days=("dias_perm", "sum"),
        )
        .reset_index()
    )
    demand["avg_stay"] = demand["total_bed_days"] / demand["admissions"].clip(lower=1)

    return demand


def load_cnes_supply(cnes_dir: Path = CNES_DIR) -> pd.DataFrame:
    """Load CNES and extract monthly bed supply per municipality and type."""
    cnes_files = sorted(cnes_dir.glob("*.parquet"))

    want_cols = ["CNES", "CODUFMUN", "QTLEITP1", "QTLEITP2", "QTLEITP3"]

    dfs = []
    for f in cnes_files:
        full_df = pd.read_parquet(f)
        use_cols = [c for c in want_cols if c in full_df.columns]
        df = full_df[use_cols].copy()

        name = f.stem
        year_str = name[4:6]
        month_str = name[6:8]
        yr = int(year_str)
        yr = yr + 2000 if yr < 50 else yr + 1900
        df["year"] = yr
        df["month"] = int(month_str)
        dfs.append(df)

    cnes = pd.concat(dfs, ignore_index=True)
    cnes["municipality"] = cnes["CODUFMUN"].astype(str).str.strip()

    for col in ["QTLEITP1", "QTLEITP2", "QTLEITP3"]:
        if col in cnes.columns:
            cnes[col] = pd.to_numeric(cnes[col], errors="coerce").fillna(0).astype(int)

    beds = (
        cnes.groupby(["municipality", "year", "month"])
        .agg(
            beds_surgical=("QTLEITP1", "sum"),
            beds_clinical=("QTLEITP2", "sum"),
            beds_obstetric=("QTLEITP3", "sum"),
        )
        .reset_index()
    )
    beds["beds_total"] = beds["beds_surgical"] + beds["beds_clinical"] + beds["beds_obstetric"]

    return beds


def calculate_occupancy(demand: pd.DataFrame, supply: pd.DataFrame) -> pd.DataFrame:
    """Calculate bed occupancy rate per municipality, month, and bed type."""
    # Pivot supply from wide to long
    supply_long = pd.melt(
        supply,
        id_vars=["municipality", "year", "month"],
        value_vars=["beds_surgical", "beds_clinical", "beds_obstetric"],
        var_name="bed_type_col",
        value_name="beds_available",
    )
    bed_type_map = {
        "beds_surgical": "surgical",
        "beds_clinical": "clinical",
        "beds_obstetric": "obstetric",
    }
    supply_long["bed_type"] = supply_long["bed_type_col"].map(bed_type_map)

    merged = demand.merge(
        supply_long[["municipality", "year", "month", "bed_type", "beds_available"]],
        on=["municipality", "year", "month", "bed_type"],
        how="left",
    )

    # Capacity = beds × days_per_month
    merged["capacity_bed_days"] = merged["beds_available"].fillna(0) * DAYS_PER_MONTH
    merged["occupancy_rate"] = merged["total_bed_days"] / merged["capacity_bed_days"].clip(lower=1)

    return merged


def calculate_beds_needed(demand: pd.DataFrame) -> pd.DataFrame:
    """Calculate beds needed per municipality and bed type based on demand and target occupancy."""
    # Use most recent 12 months of demand to project needs
    latest_year = demand["year"].max()
    recent = demand[demand["year"] == latest_year].copy()

    monthly_avg = (
        recent.groupby(["municipality", "bed_type"])
        .agg(
            avg_monthly_admissions=("admissions", "mean"),
            avg_monthly_bed_days=("total_bed_days", "mean"),
            avg_stay=("avg_stay", "mean"),
        )
        .reset_index()
    )

    # beds_needed = avg_daily_bed_days / target_occupancy
    monthly_avg["avg_daily_bed_days"] = monthly_avg["avg_monthly_bed_days"] / DAYS_PER_MONTH
    monthly_avg["beds_needed"] = np.ceil(
        monthly_avg["avg_daily_bed_days"] / TARGET_OCCUPANCY
    ).astype(int)

    return monthly_avg


def calculate_gap(beds_needed: pd.DataFrame, supply: pd.DataFrame) -> pd.DataFrame:
    """Calculate bed deficit/surplus per municipality and type."""
    latest_year = supply["year"].max()
    latest_month = supply[supply["year"] == latest_year]["month"].max()

    current_supply = supply[
        (supply["year"] == latest_year) & (supply["month"] == latest_month)
    ].copy()

    # Pivot to long
    supply_long = pd.melt(
        current_supply,
        id_vars=["municipality"],
        value_vars=["beds_surgical", "beds_clinical", "beds_obstetric"],
        var_name="bed_type_col",
        value_name="beds_available",
    )
    bed_type_map = {
        "beds_surgical": "surgical",
        "beds_clinical": "clinical",
        "beds_obstetric": "obstetric",
    }
    supply_long["bed_type"] = supply_long["bed_type_col"].map(bed_type_map)
    supply_long = supply_long.groupby(["municipality", "bed_type"])["beds_available"].sum().reset_index()

    gap = beds_needed.merge(
        supply_long,
        on=["municipality", "bed_type"],
        how="outer",
    )
    gap["beds_available"] = gap["beds_available"].fillna(0).astype(int)
    gap["beds_needed"] = gap["beds_needed"].fillna(0).astype(int)
    gap["bed_deficit"] = gap["beds_needed"] - gap["beds_available"]
    gap["deficit_pct"] = gap["bed_deficit"] / gap["beds_available"].clip(lower=1) * 100

    return gap


def estimate_doctors_needed(gap: pd.DataFrame) -> pd.DataFrame:
    """Estimate additional physicians needed based on bed deficit."""
    gap = gap.copy()
    gap["physicians_per_bed"] = gap["bed_type"].map(PHYSICIANS_PER_BED).fillna(1.0)
    gap["additional_doctors"] = np.maximum(0, gap["bed_deficit"]) * gap["physicians_per_bed"]
    gap["additional_doctors"] = np.ceil(gap["additional_doctors"]).astype(int)

    return gap


def state_level_summary(gap: pd.DataFrame) -> pd.DataFrame:
    """Aggregate gap to state level per bed type."""
    state = (
        gap.groupby("bed_type")
        .agg(
            total_beds_needed=("beds_needed", "sum"),
            total_beds_available=("beds_available", "sum"),
            total_deficit=("bed_deficit", lambda x: x[x > 0].sum()),
            total_surplus=("bed_deficit", lambda x: -x[x < 0].sum()),
            municipalities_in_deficit=("bed_deficit", lambda x: (x > 0).sum()),
            additional_doctors=("additional_doctors", "sum"),
        )
        .reset_index()
    )
    state["occupancy_at_current"] = state["total_beds_needed"] / state["total_beds_available"].clip(lower=1)
    return state

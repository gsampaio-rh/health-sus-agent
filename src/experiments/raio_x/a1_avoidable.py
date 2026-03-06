"""A1 — Avoidable Hospitalizations (ICSAP) analysis.

Classifies every SIH admission against the official ICSAP list to identify
where primary care is failing across São Paulo municipalities.

Optimized for M1 MacBook — processes files in chunks to limit memory.
"""

from pathlib import Path

import pandas as pd
import numpy as np
from loguru import logger

from src.experiments.raio_x.icsap import classify_icsap_series, get_group_name

SIH_DIR = Path("data/sih")

SIH_COLS = ["ANO_CMPT", "MES_CMPT", "DIAG_PRINC", "MUNIC_MOV", "VAL_TOT", "DIAS_PERM", "MORTE"]


def load_and_classify(sih_dir: Path = SIH_DIR) -> pd.DataFrame:
    """Load SIH admissions in chunks, classify ICSAP, and aggregate.

    Returns a pre-aggregated DataFrame (municipality × year × icsap_group)
    instead of keeping all 25M rows in memory.
    """
    sih_files = sorted(sih_dir.glob("*.parquet"))
    if not sih_files:
        raise FileNotFoundError(f"No parquet files in {sih_dir}")

    agg_chunks = []
    group_chunks = []
    total_rows = 0
    total_icsap = 0

    for i, f in enumerate(sih_files):
        df = pd.read_parquet(f, columns=SIH_COLS)
        total_rows += len(df)

        df["year"] = df["ANO_CMPT"].astype(int)
        df["municipality"] = df["MUNIC_MOV"].astype(str).str.strip()
        df["diag"] = df["DIAG_PRINC"].astype(str).str.strip()
        df["val_tot"] = pd.to_numeric(df["VAL_TOT"], errors="coerce").fillna(0)
        df["dias_perm"] = pd.to_numeric(df["DIAS_PERM"], errors="coerce").fillna(0).astype(int)
        df["morte"] = df["MORTE"].astype(str).str.strip() == "1"

        df["icsap_group"] = classify_icsap_series(df["diag"])
        df["is_icsap"] = df["icsap_group"].notna()
        total_icsap += df["is_icsap"].sum()

        chunk_agg = (
            df.groupby(["municipality", "year", "is_icsap"])
            .agg(
                admissions=("diag", "count"),
                cost=("val_tot", "sum"),
                deaths=("morte", "sum"),
                bed_days=("dias_perm", "sum"),
            )
            .reset_index()
        )
        agg_chunks.append(chunk_agg)

        icsap_only = df[df["is_icsap"]]
        if len(icsap_only) > 0:
            group_agg = (
                icsap_only.groupby("icsap_group")
                .agg(
                    admissions=("diag", "count"),
                    cost=("val_tot", "sum"),
                    deaths=("morte", "sum"),
                    bed_days=("dias_perm", "sum"),
                )
                .reset_index()
            )
            group_chunks.append(group_agg)

        if (i + 1) % 20 == 0:
            logger.info(f"  Processed {i + 1}/{len(sih_files)} files ({total_rows:,} rows)")

    logger.info(f"Loaded {total_rows:,} admissions from {len(sih_files)} files")
    logger.info(f"ICSAP admissions: {total_icsap:,} ({total_icsap / total_rows * 100:.1f}%)")

    # Combine chunk aggregations
    muni_agg = pd.concat(agg_chunks, ignore_index=True)
    muni_agg = (
        muni_agg.groupby(["municipality", "year", "is_icsap"])
        .agg(admissions=("admissions", "sum"), cost=("cost", "sum"),
             deaths=("deaths", "sum"), bed_days=("bed_days", "sum"))
        .reset_index()
    )

    group_agg = pd.concat(group_chunks, ignore_index=True)
    group_agg = (
        group_agg.groupby("icsap_group")
        .agg(admissions=("admissions", "sum"), cost=("cost", "sum"),
             deaths=("deaths", "sum"), bed_days=("bed_days", "sum"))
        .reset_index()
    )

    return muni_agg, group_agg


def summary_by_group(group_agg: pd.DataFrame) -> pd.DataFrame:
    """Top ICSAP groups by volume, cost, and mortality."""
    group_agg = group_agg.copy()
    group_agg["group_name"] = group_agg["icsap_group"].map(get_group_name)
    group_agg["avg_cost"] = group_agg["cost"] / group_agg["admissions"].clip(lower=1)
    group_agg["avg_stay"] = group_agg["bed_days"] / group_agg["admissions"].clip(lower=1)
    group_agg["mortality_rate_pct"] = group_agg["deaths"] / group_agg["admissions"] * 100
    return group_agg.sort_values("admissions", ascending=False)


def summary_state_trend(muni_agg: pd.DataFrame) -> pd.DataFrame:
    """State-level ICSAP trend by year."""
    yearly = muni_agg.groupby(["year", "is_icsap"]).agg(
        admissions=("admissions", "sum"), cost=("cost", "sum")
    ).reset_index()

    total_by_year = yearly.groupby("year")["admissions"].sum().reset_index(name="total_admissions")
    icsap_by_year = yearly[yearly["is_icsap"]].groupby("year").agg(
        icsap_admissions=("admissions", "sum"), icsap_cost=("cost", "sum")
    ).reset_index()

    trend = total_by_year.merge(icsap_by_year, on="year", how="left")
    trend["icsap_admissions"] = trend["icsap_admissions"].fillna(0).astype(int)
    trend["icsap_rate_pct"] = trend["icsap_admissions"] / trend["total_admissions"] * 100
    return trend


def muni_year_summary(muni_agg: pd.DataFrame) -> pd.DataFrame:
    """Municipality × year ICSAP rates."""
    total = muni_agg.groupby(["municipality", "year"])["admissions"].sum().reset_index(name="total_admissions")
    icsap = (
        muni_agg[muni_agg["is_icsap"]]
        .groupby(["municipality", "year"])["admissions"]
        .sum()
        .reset_index(name="icsap_admissions")
    )
    merged = total.merge(icsap, on=["municipality", "year"], how="left")
    merged["icsap_admissions"] = merged["icsap_admissions"].fillna(0).astype(int)
    merged["icsap_rate_pct"] = merged["icsap_admissions"] / merged["total_admissions"] * 100
    return merged


def top_worst_municipalities(muni_year: pd.DataFrame, year: int = 2024, min_admissions: int = 5000) -> pd.DataFrame:
    """Rank municipalities by ICSAP rate for a given year."""
    filtered = muni_year[
        (muni_year["year"] == year) & (muni_year["total_admissions"] >= min_admissions)
    ].copy()
    return filtered.sort_values("icsap_rate_pct", ascending=False)

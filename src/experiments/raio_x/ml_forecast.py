"""ML-powered demand forecasting and ICSAP risk prediction.

Uses LightGBM to:
1. Forecast hospital bed demand per municipality × bed_type for 2026-2028
2. Predict which municipalities will have worsening ICSAP rates
3. Recommend optimal resource allocation
"""

from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from loguru import logger

from src.experiments.raio_x.a1_avoidable import load_and_classify, muni_year_summary
from src.experiments.raio_x.a7_demand_supply import (
    DAYS_PER_MONTH,
    TARGET_OCCUPANCY,
    PHYSICIANS_PER_BED,
    load_cnes_supply,
    load_sih_demand,
)

SIH_DIR = Path("data/sih")
CNES_DIR = Path("data/cnes")


# ─── Feature Engineering ───────────────────────────────────────────────────────

def _build_demand_features(demand: pd.DataFrame) -> pd.DataFrame:
    """Build time-series features for demand forecasting per municipality × bed_type."""
    demand = demand.sort_values(["municipality", "bed_type", "year", "month"]).copy()

    demand["date_idx"] = (demand["year"] - 2016) * 12 + demand["month"]
    demand["month_sin"] = np.sin(2 * np.pi * demand["month"] / 12)
    demand["month_cos"] = np.cos(2 * np.pi * demand["month"] / 12)
    demand["is_winter"] = demand["month"].isin([6, 7, 8]).astype(int)
    demand["is_covid"] = ((demand["year"] == 2020) | (demand["year"] == 2021)).astype(int)
    demand["year_idx"] = demand["year"] - 2016

    for col in ["admissions", "total_bed_days"]:
        for lag in [1, 2, 3, 6, 12]:
            demand[f"{col}_lag{lag}"] = (
                demand.groupby(["municipality", "bed_type"])[col]
                .shift(lag)
            )
        for window in [3, 6, 12]:
            demand[f"{col}_roll{window}_mean"] = (
                demand.groupby(["municipality", "bed_type"])[col]
                .transform(lambda x: x.shift(1).rolling(window, min_periods=1).mean())
            )
            demand[f"{col}_roll{window}_std"] = (
                demand.groupby(["municipality", "bed_type"])[col]
                .transform(lambda x: x.shift(1).rolling(window, min_periods=1).std())
            )

    # Same month last year
    demand["admissions_same_month_ly"] = demand.groupby(["municipality", "bed_type", "month"])["admissions"].shift(1)

    return demand


DEMAND_FEATURES = [
    "date_idx", "month_sin", "month_cos", "is_winter", "is_covid", "year_idx",
    "admissions_lag1", "admissions_lag2", "admissions_lag3", "admissions_lag6", "admissions_lag12",
    "admissions_roll3_mean", "admissions_roll6_mean", "admissions_roll12_mean",
    "admissions_roll3_std", "admissions_roll6_std", "admissions_roll12_std",
    "total_bed_days_lag1", "total_bed_days_lag12",
    "total_bed_days_roll3_mean", "total_bed_days_roll12_mean",
    "admissions_same_month_ly",
]


def train_demand_forecaster(demand: pd.DataFrame) -> tuple[lgb.Booster, pd.DataFrame]:
    """Train LightGBM to forecast monthly admissions per municipality × bed_type."""
    featured = _build_demand_features(demand)

    available = [c for c in DEMAND_FEATURES if c in featured.columns]

    train = featured[(featured["year"] >= 2017) & (featured["year"] <= 2023)].dropna(subset=available + ["admissions"])
    val = featured[featured["year"] == 2024].dropna(subset=available + ["admissions"])
    test = featured[featured["year"] == 2025].dropna(subset=available + ["admissions"])

    X_train = train[available].fillna(0)
    y_train = train["admissions"].values.astype(float)
    X_val = val[available].fillna(0)
    y_val = val["admissions"].values.astype(float)

    logger.info(f"Training demand forecaster: {len(X_train):,} train, {len(X_val):,} val")

    dtrain = lgb.Dataset(X_train, label=y_train)
    dval = lgb.Dataset(X_val, label=y_val, reference=dtrain)

    params = {
        "objective": "regression",
        "metric": "mape",
        "learning_rate": 0.05,
        "num_leaves": 63,
        "min_child_samples": 30,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "verbose": -1,
        "seed": 42,
    }

    model = lgb.train(
        params, dtrain,
        num_boost_round=500,
        valid_sets=[dval],
        callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)],
    )

    # Evaluate on test
    if len(test) > 0:
        X_test = test[available].fillna(0)
        y_test = test["admissions"].values.astype(float)
        preds = model.predict(X_test)
        mask = y_test > 0
        mape = np.mean(np.abs(y_test[mask] - preds[mask]) / y_test[mask]) * 100
        logger.info(f"Demand forecaster test MAPE: {mape:.1f}%")

    return model, featured


def project_future_demand(
    model: lgb.Booster,
    historical: pd.DataFrame,
    years: list[int] = [2026, 2027, 2028],
) -> pd.DataFrame:
    """Project demand forward using iterative forecasting."""
    available = [c for c in DEMAND_FEATURES if c in historical.columns]

    projections = []
    working = historical.copy()

    for year in years:
        for month in range(1, 13):
            future_rows = []
            for (muni, btype), group in working.groupby(["municipality", "bed_type"]):
                group = group.sort_values(["year", "month"])
                last = group.iloc[-1]

                row = {
                    "municipality": muni,
                    "bed_type": btype,
                    "year": year,
                    "month": month,
                    "date_idx": (year - 2016) * 12 + month,
                    "month_sin": np.sin(2 * np.pi * month / 12),
                    "month_cos": np.cos(2 * np.pi * month / 12),
                    "is_winter": int(month in [6, 7, 8]),
                    "is_covid": 0,
                    "year_idx": year - 2016,
                }

                recent = group.tail(12)
                for lag in [1, 2, 3, 6, 12]:
                    idx = -lag
                    if abs(idx) <= len(group):
                        row[f"admissions_lag{lag}"] = group.iloc[idx]["admissions"]
                        if lag in [1, 12]:
                            row[f"total_bed_days_lag{lag}"] = group.iloc[idx]["total_bed_days"]
                    else:
                        row[f"admissions_lag{lag}"] = 0
                        if lag in [1, 12]:
                            row[f"total_bed_days_lag{lag}"] = 0

                for window in [3, 6, 12]:
                    vals = group["admissions"].tail(window).values
                    row[f"admissions_roll{window}_mean"] = vals.mean() if len(vals) > 0 else 0
                    row[f"admissions_roll{window}_std"] = vals.std() if len(vals) > 1 else 0
                    if window in [3, 12]:
                        bd_vals = group["total_bed_days"].tail(window).values
                        row[f"total_bed_days_roll{window}_mean"] = bd_vals.mean() if len(bd_vals) > 0 else 0

                same_month = group[group["month"] == month]
                row["admissions_same_month_ly"] = same_month.iloc[-1]["admissions"] if len(same_month) > 0 else 0

                future_rows.append(row)

            future_df = pd.DataFrame(future_rows)
            X_future = future_df[available].fillna(0)
            future_df["admissions"] = np.maximum(0, model.predict(X_future)).astype(int)

            # Estimate bed days from avg stay
            avg_stay_by_type = working.groupby("bed_type")["avg_stay"].mean()
            future_df["avg_stay"] = future_df["bed_type"].map(avg_stay_by_type).fillna(5)
            future_df["total_bed_days"] = (future_df["admissions"] * future_df["avg_stay"]).astype(int)

            projections.append(future_df)

            # Append to working set for next iteration
            working = pd.concat([working, future_df], ignore_index=True)

        logger.info(f"Projected {year}: {len(future_df):,} municipality × bed_type combinations")

    return pd.concat(projections, ignore_index=True)


def compute_future_gap(projections: pd.DataFrame, current_supply: pd.DataFrame) -> pd.DataFrame:
    """Compute bed gap for projected future years."""
    latest_year = current_supply["year"].max()
    latest_month = current_supply[current_supply["year"] == latest_year]["month"].max()

    current_beds = current_supply[
        (current_supply["year"] == latest_year) & (current_supply["month"] == latest_month)
    ].copy()

    supply_long = pd.melt(
        current_beds,
        id_vars=["municipality"],
        value_vars=["beds_surgical", "beds_clinical", "beds_obstetric"],
        var_name="bed_type_col", value_name="beds_available",
    )
    supply_long["bed_type"] = supply_long["bed_type_col"].map({
        "beds_surgical": "surgical", "beds_clinical": "clinical", "beds_obstetric": "obstetric",
    })
    supply_long = supply_long.groupby(["municipality", "bed_type"])["beds_available"].sum().reset_index()

    annual = (
        projections.groupby(["municipality", "bed_type", "year"])
        .agg(
            avg_monthly_admissions=("admissions", "mean"),
            avg_monthly_bed_days=("total_bed_days", "mean"),
        )
        .reset_index()
    )
    annual["avg_daily_bed_days"] = annual["avg_monthly_bed_days"] / DAYS_PER_MONTH
    annual["beds_needed"] = np.ceil(annual["avg_daily_bed_days"] / TARGET_OCCUPANCY).astype(int)

    gap = annual.merge(supply_long, on=["municipality", "bed_type"], how="left")
    gap["beds_available"] = gap["beds_available"].fillna(0).astype(int)
    gap["bed_deficit"] = gap["beds_needed"] - gap["beds_available"]
    gap["physicians_per_bed"] = gap["bed_type"].map(PHYSICIANS_PER_BED).fillna(1.0)
    gap["additional_doctors"] = np.maximum(0, gap["bed_deficit"]) * gap["physicians_per_bed"]
    gap["additional_doctors"] = np.ceil(gap["additional_doctors"]).astype(int)

    return gap


# ─── ICSAP Risk Model ─────────────────────────────────────────────────────────

def _build_icsap_risk_features(
    muni_year: pd.DataFrame,
    supply: pd.DataFrame,
) -> pd.DataFrame:
    """Build features to predict next-year ICSAP rate per municipality."""
    df = muni_year.copy()

    df["icsap_rate_lag1"] = df.groupby("municipality")["icsap_rate_pct"].shift(1)
    df["icsap_rate_lag2"] = df.groupby("municipality")["icsap_rate_pct"].shift(2)
    df["icsap_rate_delta"] = df["icsap_rate_lag1"] - df["icsap_rate_lag2"]
    df["icsap_rate_roll3"] = (
        df.groupby("municipality")["icsap_rate_pct"]
        .transform(lambda x: x.shift(1).rolling(3, min_periods=1).mean())
    )
    df["total_adm_lag1"] = df.groupby("municipality")["total_admissions"].shift(1)
    df["total_adm_growth"] = (
        df["total_adm_lag1"] /
        df.groupby("municipality")["total_admissions"].shift(2).clip(lower=1)
    )

    # Merge CNES bed supply (annual average)
    annual_beds = (
        supply.groupby(["municipality", "year"])
        .agg(beds_total=("beds_total", "mean"), n_months=("month", "count"))
        .reset_index()
    )
    df = df.merge(annual_beds[["municipality", "year", "beds_total"]], on=["municipality", "year"], how="left")
    df["beds_per_1k_adm"] = df["beds_total"] / (df["total_admissions"] / 1000).clip(lower=0.1)

    df["year_idx"] = df["year"] - 2016

    return df


ICSAP_RISK_FEATURES = [
    "icsap_rate_lag1", "icsap_rate_lag2", "icsap_rate_delta", "icsap_rate_roll3",
    "total_adm_lag1", "total_adm_growth", "beds_total", "beds_per_1k_adm", "year_idx",
]


def train_icsap_risk_model(
    muni_year: pd.DataFrame,
    supply: pd.DataFrame,
) -> tuple[lgb.Booster, pd.DataFrame]:
    """Train a model to predict next-year ICSAP rate per municipality."""
    featured = _build_icsap_risk_features(muni_year, supply)

    available = [c for c in ICSAP_RISK_FEATURES if c in featured.columns]

    train = featured[(featured["year"] >= 2018) & (featured["year"] <= 2023)].dropna(subset=available + ["icsap_rate_pct"])
    val = featured[featured["year"] == 2024].dropna(subset=available + ["icsap_rate_pct"])

    X_train = train[available].fillna(0)
    y_train = train["icsap_rate_pct"].values
    X_val = val[available].fillna(0)
    y_val = val["icsap_rate_pct"].values

    logger.info(f"Training ICSAP risk model: {len(X_train):,} train, {len(X_val):,} val")

    dtrain = lgb.Dataset(X_train, label=y_train)
    dval = lgb.Dataset(X_val, label=y_val, reference=dtrain)

    params = {
        "objective": "regression",
        "metric": "mae",
        "learning_rate": 0.05,
        "num_leaves": 31,
        "min_child_samples": 10,
        "feature_fraction": 0.8,
        "verbose": -1,
        "seed": 42,
    }

    model = lgb.train(
        params, dtrain,
        num_boost_round=300,
        valid_sets=[dval],
        callbacks=[lgb.early_stopping(30), lgb.log_evaluation(100)],
    )

    preds = model.predict(X_val)
    mae = np.mean(np.abs(y_val - preds))
    logger.info(f"ICSAP risk model val MAE: {mae:.2f} percentage points")

    return model, featured


def predict_icsap_risk(
    model: lgb.Booster,
    featured: pd.DataFrame,
    target_year: int = 2025,
) -> pd.DataFrame:
    """Predict ICSAP rate for a target year and flag municipalities at risk."""
    available = [c for c in ICSAP_RISK_FEATURES if c in featured.columns]

    target = featured[featured["year"] == target_year].dropna(subset=available)
    if len(target) == 0:
        logger.warning(f"No data for year {target_year}")
        return pd.DataFrame()

    X = target[available].fillna(0)
    target = target.copy()
    target["predicted_icsap_rate"] = model.predict(X)
    target["risk_delta"] = target["predicted_icsap_rate"] - target["icsap_rate_lag1"]
    target["risk_category"] = pd.cut(
        target["predicted_icsap_rate"],
        bins=[0, 12, 16, 22, 100],
        labels=["low", "moderate", "high", "critical"],
    )

    return target.sort_values("predicted_icsap_rate", ascending=False)


# ─── Resource Allocation Optimizer ─────────────────────────────────────────────

def optimize_allocation(
    future_gap: pd.DataFrame,
    icsap_risk: pd.DataFrame,
    budget_beds: int = 5000,
) -> pd.DataFrame:
    """Greedy allocation: prioritize municipalities by combined need score.

    Score = bed_deficit × icsap_risk_rate (municipalities that need beds AND
    have high avoidable hospitalization rates get priority).
    """
    gap_2027 = future_gap[future_gap["year"] == 2027].copy()

    muni_gap = (
        gap_2027[gap_2027["bed_deficit"] > 0]
        .groupby("municipality")
        .agg(
            total_deficit=("bed_deficit", "sum"),
            beds_needed=("beds_needed", "sum"),
            beds_available=("beds_available", "sum"),
            doctors_needed=("additional_doctors", "sum"),
        )
        .reset_index()
    )

    if len(icsap_risk) > 0:
        risk_scores = icsap_risk[["municipality", "predicted_icsap_rate", "risk_category"]].drop_duplicates("municipality")
        muni_gap = muni_gap.merge(risk_scores, on="municipality", how="left")
        muni_gap["predicted_icsap_rate"] = muni_gap["predicted_icsap_rate"].fillna(14)
    else:
        muni_gap["predicted_icsap_rate"] = 14
        muni_gap["risk_category"] = "moderate"

    # Combined priority score: deficit × ICSAP rate (higher = more urgent)
    muni_gap["priority_score"] = muni_gap["total_deficit"] * muni_gap["predicted_icsap_rate"]
    muni_gap = muni_gap.sort_values("priority_score", ascending=False)

    # Greedy allocation
    remaining = budget_beds
    allocations = []
    for _, row in muni_gap.iterrows():
        if remaining <= 0:
            break
        alloc = min(int(row["total_deficit"]), remaining)
        allocations.append({
            "municipality": row["municipality"],
            "beds_allocated": alloc,
            "deficit_before": int(row["total_deficit"]),
            "deficit_after": int(row["total_deficit"]) - alloc,
            "icsap_risk": row["predicted_icsap_rate"],
            "risk_category": row["risk_category"],
            "priority_score": row["priority_score"],
        })
        remaining -= alloc

    result = pd.DataFrame(allocations)
    logger.info(
        f"Allocated {budget_beds - remaining:,} beds across {len(result):,} municipalities "
        f"(budget: {budget_beds:,})"
    )
    return result

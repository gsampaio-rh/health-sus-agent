import numpy as np
import pandas as pd


LAG_MONTHS = [1, 2, 3, 6, 12]
ROLLING_WINDOWS = [3, 6, 12]


def add_lag_features(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    df = df.copy()
    df = df.sort_values(group_cols + ["year", "month"])

    for lag in LAG_MONTHS:
        df[f"adm_lag_{lag}"] = df.groupby(group_cols)["admissions"].shift(lag)

    return df


def add_rolling_features(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    df = df.copy()
    df = df.sort_values(group_cols + ["year", "month"])

    for window in ROLLING_WINDOWS:
        df[f"adm_rolling_mean_{window}"] = df.groupby(group_cols)["admissions"].transform(
            lambda x: x.shift(1).rolling(window, min_periods=1).mean()
        )
        df[f"adm_rolling_std_{window}"] = df.groupby(group_cols)["admissions"].transform(
            lambda x: x.shift(1).rolling(window, min_periods=1).std()
        )

    return df


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    df["year_index"] = df["year"] - df["year"].min()
    df["is_winter"] = df["month"].isin([6, 7, 8]).astype(int)
    df["is_covid_period"] = ((df["year"] == 2020) | (df["year"] == 2021)).astype(int)
    return df


def add_same_month_last_year(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    df = df.copy()
    prev = df[group_cols + ["year", "month", "admissions"]].copy()
    prev["year"] = prev["year"] + 1
    prev = prev.rename(columns={"admissions": "adm_same_month_last_year"})

    df = df.merge(
        prev[group_cols + ["year", "month", "adm_same_month_last_year"]],
        on=group_cols + ["year", "month"],
        how="left",
    )
    return df


def build_feature_matrix(
    demand: pd.DataFrame,
    beds: pd.DataFrame | None = None,
    group_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Full feature engineering pipeline for demand forecasting."""
    if group_cols is None:
        group_cols = ["municipality", "espec"]

    df = add_lag_features(demand, group_cols)
    df = add_rolling_features(df, group_cols)
    df = add_calendar_features(df)
    df = add_same_month_last_year(df, group_cols)

    if beds is not None:
        df = df.merge(
            beds,
            on=["municipality", "year", "month"],
            how="left",
        )
        for col in ["beds_surgical", "beds_clinical", "beds_obstetric", "beds_total_sus", "n_facilities"]:
            if col in df.columns:
                df[col] = df[col].fillna(0)

    return df


FEATURE_COLUMNS = (
    [f"adm_lag_{lag}" for lag in LAG_MONTHS]
    + [f"adm_rolling_mean_{w}" for w in ROLLING_WINDOWS]
    + [f"adm_rolling_std_{w}" for w in ROLLING_WINDOWS]
    + [
        "month_sin",
        "month_cos",
        "year_index",
        "is_winter",
        "is_covid_period",
        "adm_same_month_last_year",
    ]
)

FEATURE_COLUMNS_WITH_BEDS = FEATURE_COLUMNS + [
    "beds_surgical",
    "beds_clinical",
    "beds_obstetric",
    "beds_total_sus",
    "n_facilities",
]

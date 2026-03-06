import pandas as pd
import numpy as np

LAG_WEEKS = [1, 2, 3, 4, 6, 8]
ROLLING_WINDOWS = [4, 8, 12]


def add_lag_features(df: pd.DataFrame, group_col: str = "municipality") -> pd.DataFrame:
    """Add lagged case counts per municipality."""
    df = df.copy()
    df = df.sort_values([group_col, "epi_year", "epi_week"])

    for lag in LAG_WEEKS:
        df[f"cases_lag_{lag}"] = df.groupby(group_col)["cases"].shift(lag)

    return df


def add_rolling_features(df: pd.DataFrame, group_col: str = "municipality") -> pd.DataFrame:
    """Add rolling mean/std of case counts per municipality."""
    df = df.copy()
    df = df.sort_values([group_col, "epi_year", "epi_week"])

    for window in ROLLING_WINDOWS:
        rolled = df.groupby(group_col)["cases"].transform(
            lambda x: x.shift(1).rolling(window, min_periods=1).mean()
        )
        df[f"cases_rolling_mean_{window}"] = rolled

        rolled_std = df.groupby(group_col)["cases"].transform(
            lambda x: x.shift(1).rolling(window, min_periods=1).std()
        )
        df[f"cases_rolling_std_{window}"] = rolled_std

    return df


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add calendar-based features."""
    df = df.copy()
    df["month"] = ((df["epi_week"] - 1) * 7 // 30 + 1).clip(1, 12)
    df["is_rainy_season"] = df["month"].isin([10, 11, 12, 1, 2, 3]).astype(int)
    df["epi_week_sin"] = np.sin(2 * np.pi * df["epi_week"] / 52)
    df["epi_week_cos"] = np.cos(2 * np.pi * df["epi_week"] / 52)
    df["year_index"] = df["epi_year"] - df["epi_year"].min()
    return df


def add_same_week_last_year(df: pd.DataFrame, group_col: str = "municipality") -> pd.DataFrame:
    """Add case count from same epidemiological week in previous year."""
    df = df.copy()
    prev_year = df[["municipality", "epi_year", "epi_week", "cases"]].copy()
    prev_year["epi_year"] = prev_year["epi_year"] + 1
    prev_year = prev_year.rename(columns={"cases": "cases_same_week_last_year"})

    df = df.merge(
        prev_year[["municipality", "epi_year", "epi_week", "cases_same_week_last_year"]],
        on=["municipality", "epi_year", "epi_week"],
        how="left",
    )
    return df


def create_forecast_target(
    df: pd.DataFrame, horizon: int, group_col: str = "municipality"
) -> pd.DataFrame:
    """Shift the target column forward to create a forecast target.

    For horizon=4, the target for row t is the value at t+4.
    """
    df = df.copy()
    df = df.sort_values([group_col, "epi_year", "epi_week"])

    df[f"target_cases_{horizon}w"] = df.groupby(group_col)["cases"].shift(-horizon)
    df[f"target_epidemic_{horizon}w"] = df.groupby(group_col)["is_epidemic"].shift(-horizon)

    return df


def build_feature_matrix(weekly: pd.DataFrame, horizon: int = 4) -> pd.DataFrame:
    """Full feature engineering pipeline."""
    df = add_lag_features(weekly)
    df = add_rolling_features(df)
    df = add_calendar_features(df)
    df = add_same_week_last_year(df)
    df = create_forecast_target(df, horizon=horizon)
    df = df.dropna(subset=[f"target_epidemic_{horizon}w"])

    return df


FEATURE_COLUMNS = (
    [f"cases_lag_{lag}" for lag in LAG_WEEKS]
    + [f"cases_rolling_mean_{w}" for w in ROLLING_WINDOWS]
    + [f"cases_rolling_std_{w}" for w in ROLLING_WINDOWS]
    + [
        "epi_week_sin",
        "epi_week_cos",
        "is_rainy_season",
        "year_index",
        "cases_same_week_last_year",
        "population",
    ]
)

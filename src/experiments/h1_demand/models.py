import numpy as np
import pandas as pd
from dataclasses import dataclass


@dataclass
class ForecastResult:
    name: str
    y_true: np.ndarray
    y_pred: np.ndarray


def seasonal_naive_forecast(df_train: pd.DataFrame, df_test: pd.DataFrame) -> ForecastResult:
    """Predict same month from previous year."""
    y_true = df_test["admissions"].values

    if "adm_same_month_last_year" in df_test.columns:
        y_pred = df_test["adm_same_month_last_year"].fillna(
            df_train["admissions"].mean()
        ).values
    else:
        y_pred = np.full_like(y_true, df_train["admissions"].mean(), dtype=float)

    return ForecastResult(name="seasonal_naive", y_true=y_true, y_pred=y_pred)


def historical_mean_forecast(df_train: pd.DataFrame, df_test: pd.DataFrame, group_cols: list[str]) -> ForecastResult:
    """Predict the historical monthly mean per group."""
    y_true = df_test["admissions"].values

    monthly_means = df_train.groupby(group_cols + ["month"])["admissions"].mean().reset_index()
    monthly_means = monthly_means.rename(columns={"admissions": "pred"})

    merged = df_test.merge(monthly_means, on=group_cols + ["month"], how="left")
    y_pred = merged["pred"].fillna(df_train["admissions"].mean()).values

    return ForecastResult(name="historical_mean", y_true=y_true, y_pred=y_pred)


def train_lightgbm_regressor(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_test: pd.DataFrame,
    y_test: np.ndarray,
) -> ForecastResult:
    import lightgbm as lgb

    model = lgb.LGBMRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=8,
        num_leaves=63,
        random_state=42,
        verbose=-1,
        n_jobs=-1,
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_test, y_test)],
        callbacks=[lgb.early_stopping(50, verbose=False)],
    )

    y_pred = model.predict(X_test)
    y_pred = np.clip(y_pred, 0, None)

    return ForecastResult(name="lightgbm", y_true=y_test, y_pred=y_pred)

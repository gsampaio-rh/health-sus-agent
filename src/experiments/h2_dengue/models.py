import numpy as np
import pandas as pd
from dataclasses import dataclass


@dataclass
class ModelResult:
    name: str
    y_true: np.ndarray
    y_pred: np.ndarray
    y_prob: np.ndarray | None = None


def majority_class_baseline(y_train: np.ndarray, y_test: np.ndarray) -> ModelResult:
    """Always predict the majority class (non-epidemic)."""
    majority = int(pd.Series(y_train).mode().iloc[0])
    y_pred = np.full_like(y_test, majority)
    majority_prob = (y_train == 1).mean()
    y_prob = np.full(len(y_test), majority_prob)

    return ModelResult(
        name="majority_class",
        y_true=y_test,
        y_pred=y_pred,
        y_prob=y_prob,
    )


def seasonal_naive_baseline(
    df_train: pd.DataFrame, df_test: pd.DataFrame, horizon: int
) -> ModelResult:
    """Predict same epidemiological week from previous year."""
    target_col = f"target_epidemic_{horizon}w"
    y_test = df_test[target_col].values

    if "cases_same_week_last_year" in df_test.columns:
        pred_cases = df_test["cases_same_week_last_year"].fillna(0).values
        threshold_rate = 300.0 / 52.0
        population = df_test["population"].values
        pred_incidence = pred_cases / population * 100_000
        y_pred = (pred_incidence >= threshold_rate).astype(int)
        y_prob = np.clip(pred_incidence / (threshold_rate * 2), 0, 1)
    else:
        y_pred = np.zeros_like(y_test)
        y_prob = np.full(len(y_test), 0.0)

    return ModelResult(
        name="seasonal_naive",
        y_true=y_test,
        y_pred=y_pred,
        y_prob=y_prob,
    )


def train_lightgbm(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_test: pd.DataFrame,
    y_test: np.ndarray,
) -> ModelResult:
    import lightgbm as lgb

    scale_pos = (y_train == 0).sum() / max((y_train == 1).sum(), 1)

    model = lgb.LGBMClassifier(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=6,
        num_leaves=31,
        scale_pos_weight=scale_pos,
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
    y_prob = model.predict_proba(X_test)[:, 1]

    return ModelResult(
        name="lightgbm",
        y_true=y_test,
        y_pred=y_pred,
        y_prob=y_prob,
    )


def train_xgboost(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_test: pd.DataFrame,
    y_test: np.ndarray,
) -> ModelResult:
    from xgboost import XGBClassifier

    scale_pos = (y_train == 0).sum() / max((y_train == 1).sum(), 1)

    model = XGBClassifier(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=6,
        scale_pos_weight=scale_pos,
        random_state=42,
        verbosity=0,
        n_jobs=-1,
        eval_metric="logloss",
        early_stopping_rounds=50,
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    return ModelResult(
        name="xgboost",
        y_true=y_test,
        y_pred=y_pred,
        y_prob=y_prob,
    )

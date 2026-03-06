import numpy as np
from dataclasses import dataclass

from src.experiments.h1_demand.models import ForecastResult

N_BOOTSTRAP = 1000
RANDOM_SEED = 42


@dataclass
class MetricWithCI:
    value: float
    ci_lower: float
    ci_upper: float

    def __str__(self) -> str:
        return f"{self.value:.2f} [{self.ci_lower:.2f}, {self.ci_upper:.2f}]"


@dataclass
class ForecastReport:
    model_name: str
    mape: MetricWithCI
    rmse: MetricWithCI
    mae: MetricWithCI
    within_15pct: MetricWithCI
    n_samples: int
    mean_actual: float


def _safe_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true > 0
    if mask.sum() == 0:
        return 0.0
    return np.mean(np.abs(y_true[mask] - y_pred[mask]) / y_true[mask]) * 100


def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return np.sqrt(np.mean((y_true - y_pred) ** 2))


def _mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return np.mean(np.abs(y_true - y_pred))


def _within_pct(y_true: np.ndarray, y_pred: np.ndarray, pct: float = 0.15) -> float:
    mask = y_true > 0
    if mask.sum() == 0:
        return 0.0
    rel_err = np.abs(y_true[mask] - y_pred[mask]) / y_true[mask]
    return (rel_err <= pct).mean() * 100


def _bootstrap_metric(y_true, y_pred, metric_fn, n_bootstrap=N_BOOTSTRAP):
    rng = np.random.RandomState(RANDOM_SEED)
    n = len(y_true)
    observed = metric_fn(y_true, y_pred)

    boot_values = []
    for _ in range(n_bootstrap):
        idx = rng.randint(0, n, size=n)
        try:
            boot_values.append(metric_fn(y_true[idx], y_pred[idx]))
        except Exception:
            continue

    if not boot_values:
        return MetricWithCI(observed, observed, observed)

    return MetricWithCI(
        value=observed,
        ci_lower=np.percentile(boot_values, 2.5),
        ci_upper=np.percentile(boot_values, 97.5),
    )


def evaluate_forecast(result: ForecastResult) -> ForecastReport:
    y_true = result.y_true.astype(float)
    y_pred = result.y_pred.astype(float)

    return ForecastReport(
        model_name=result.name,
        mape=_bootstrap_metric(y_true, y_pred, _safe_mape),
        rmse=_bootstrap_metric(y_true, y_pred, _rmse),
        mae=_bootstrap_metric(y_true, y_pred, _mae),
        within_15pct=_bootstrap_metric(y_true, y_pred, _within_pct),
        n_samples=len(y_true),
        mean_actual=y_true.mean(),
    )


def format_report(report: ForecastReport) -> str:
    return (
        f"=== {report.model_name} ===\n"
        f"N={report.n_samples:,} | Mean actual: {report.mean_actual:.1f} admissions\n"
        f"MAPE:       {report.mape}%\n"
        f"RMSE:       {report.rmse}\n"
        f"MAE:        {report.mae}\n"
        f"Within 15%: {report.within_15pct}%"
    )

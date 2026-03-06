import numpy as np
from dataclasses import dataclass

from sklearn.metrics import (
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
)

from src.experiments.h2_dengue.models import ModelResult

N_BOOTSTRAP = 1000
RANDOM_SEED = 42


@dataclass
class MetricWithCI:
    value: float
    ci_lower: float
    ci_upper: float

    def __str__(self) -> str:
        return f"{self.value:.3f} [{self.ci_lower:.3f}, {self.ci_upper:.3f}]"


@dataclass
class EvaluationReport:
    model_name: str
    horizon: int
    f1: MetricWithCI
    precision: MetricWithCI
    recall: MetricWithCI
    auc_roc: MetricWithCI
    auc_pr: MetricWithCI
    confusion: np.ndarray
    n_samples: int
    epidemic_prevalence: float


def _bootstrap_metric(y_true: np.ndarray, y_score: np.ndarray, metric_fn, n_bootstrap: int = N_BOOTSTRAP) -> MetricWithCI:
    """Compute a metric with bootstrap 95% confidence interval."""
    rng = np.random.RandomState(RANDOM_SEED)
    n = len(y_true)
    observed = metric_fn(y_true, y_score)

    boot_values = []
    for _ in range(n_bootstrap):
        idx = rng.randint(0, n, size=n)
        y_t = y_true[idx]
        y_s = y_score[idx]
        if len(np.unique(y_t)) < 2:
            continue
        try:
            boot_values.append(metric_fn(y_t, y_s))
        except Exception:
            continue

    if not boot_values:
        return MetricWithCI(value=observed, ci_lower=observed, ci_upper=observed)

    ci_lower = np.percentile(boot_values, 2.5)
    ci_upper = np.percentile(boot_values, 97.5)
    return MetricWithCI(value=observed, ci_lower=ci_lower, ci_upper=ci_upper)


def evaluate_model(result: ModelResult, horizon: int) -> EvaluationReport:
    """Full evaluation of a model result with bootstrap CIs."""
    y_true = result.y_true.astype(int)
    y_pred = result.y_pred.astype(int)
    y_prob = result.y_prob if result.y_prob is not None else y_pred.astype(float)

    f1 = _bootstrap_metric(y_true, y_pred, f1_score)
    precision = _bootstrap_metric(y_true, y_pred, precision_score)
    recall = _bootstrap_metric(y_true, y_pred, recall_score)

    try:
        auc_roc = _bootstrap_metric(y_true, y_prob, roc_auc_score)
    except ValueError:
        auc_roc = MetricWithCI(0.0, 0.0, 0.0)

    try:
        auc_pr = _bootstrap_metric(y_true, y_prob, average_precision_score)
    except ValueError:
        auc_pr = MetricWithCI(0.0, 0.0, 0.0)

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    prevalence = y_true.mean()

    return EvaluationReport(
        model_name=result.name,
        horizon=horizon,
        f1=f1,
        precision=precision,
        recall=recall,
        auc_roc=auc_roc,
        auc_pr=auc_pr,
        confusion=cm,
        n_samples=len(y_true),
        epidemic_prevalence=prevalence,
    )


def format_report(report: EvaluationReport) -> str:
    lines = [
        f"=== {report.model_name} | Horizon: {report.horizon}w ===",
        f"N={report.n_samples:,} | Epidemic prevalence: {report.epidemic_prevalence:.1%}",
        f"F1:        {report.f1}",
        f"Precision: {report.precision}",
        f"Recall:    {report.recall}",
        f"AUC-ROC:   {report.auc_roc}",
        f"AUC-PR:    {report.auc_pr}",
        f"Confusion matrix:",
        f"  TN={report.confusion[0,0]:,}  FP={report.confusion[0,1]:,}",
        f"  FN={report.confusion[1,0]:,}  TP={report.confusion[1,1]:,}",
    ]
    return "\n".join(lines)

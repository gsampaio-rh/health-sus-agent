"""Analysis tools — aggregations, time series, cross-tabs, statistics.

Each tool operates on a named dataset from the data registry and returns
a human-readable string result that the LLM can interpret.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from src.agent.tools.data import get_dataset


def aggregate(
    dataset: str,
    group_by: list[str],
    metrics: dict[str, str],
    sort_by: str | None = None,
    top_n: int = 20,
    new_name: str | None = None,
) -> str:
    """Group-by aggregation on a dataset.

    Args:
        dataset: Name of a loaded dataset.
        group_by: Columns to group by. Use ["__all__"] for whole-dataset stats.
        metrics: Map of output_name -> "column:agg_func".
            e.g. {"mortality_rate": "MORTE:mean", "count": "MORTE:count"}
        sort_by: Column to sort results by (descending).
        top_n: Max rows to return.
        new_name: If provided, save the result as a new dataset with this name.

    Returns:
        Formatted table string.
    """
    from src.agent.tools.data import _DATASETS

    df = get_dataset(dataset)

    def _parse_metric(spec: str) -> tuple[str, str] | str:
        """Parse 'col:func' spec. Supports '*:count' and ':count' for row counts."""
        if spec in ("*:count", ":count", "count", "*count"):
            first_col = df.columns[0]
            return (first_col, "count")
        parts = spec.split(":")
        if len(parts) != 2:
            return (
                f"Error: metric spec '{spec}' must be 'column:agg_func' "
                f"(e.g. 'MORTE:mean', 'MORTE:count', '*:count'). "
                f"Valid agg funcs: count, sum, mean, median, min, max, std"
            )
        col, func = parts
        if col == "*" or col == "":
            col = df.columns[0]
        if col not in df.columns:
            return f"Error: column '{col}' not in dataset"
        return (col, func)

    if not group_by or group_by == ["__all__"]:
        agg_results = {}
        for out_name, spec in metrics.items():
            parsed = _parse_metric(spec)
            if isinstance(parsed, str):
                return parsed
            col, func = parsed
            agg_results[out_name] = df[col].agg(func)
        lines = [f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}"
                 for k, v in agg_results.items()]
        return "Whole-dataset aggregation:\n" + "\n".join(lines)

    for col in group_by:
        if col not in df.columns:
            return f"Error: column '{col}' not in dataset"

    agg_dict: dict[str, tuple[str, str]] = {}
    for out_name, spec in metrics.items():
        parsed = _parse_metric(spec)
        if isinstance(parsed, str):
            return parsed
        agg_dict[out_name] = parsed

    result = df.groupby(group_by, dropna=False).agg(
        **{name: pd.NamedAgg(column=col, aggfunc=func)
           for name, (col, func) in agg_dict.items()}
    ).reset_index()

    if sort_by and sort_by in result.columns:
        result = result.sort_values(sort_by, ascending=False)

    result = result.head(top_n)

    for col in result.select_dtypes(include="float").columns:
        result[col] = result[col].round(4)

    if new_name:
        _DATASETS[new_name] = result

    output = result.to_string(index=False)
    if new_name:
        output += (
            f"\n(Saved as dataset '{new_name}': {len(result)} rows, "
            f"columns={list(result.columns)})"
        )
    return output


def _safe_parse_dates(series: pd.Series) -> pd.Series:
    """Parse date column trying common SUS formats."""
    if series.dtype in ("int32", "int64", "float64"):
        return series

    for fmt in ("%Y%m%d", "%d%m%Y", "%Y-%m-%d", None):
        try:
            return pd.to_datetime(series, format=fmt, errors="coerce")
        except (ValueError, TypeError):
            continue
    return pd.to_datetime(series, errors="coerce")


def time_series(
    dataset: str,
    date_col: str,
    value_col: str,
    freq: str = "year",
    agg_func: str = "mean",
    new_name: str | None = None,
) -> str:
    """Analyze temporal trends in a dataset.

    Args:
        dataset: Name of a loaded dataset.
        date_col: Column containing dates or year integers.
        value_col: Column to aggregate.
        freq: "year", "month", "Y", or "M".
        agg_func: Aggregation function ("mean", "sum", "count").
        new_name: If provided, save the trend table as a new dataset.

    Returns:
        Trend table with change detection.
    """
    from src.agent.tools.data import _DATASETS

    df = get_dataset(dataset)

    if date_col not in df.columns:
        return f"Error: column '{date_col}' not in dataset"
    if value_col not in df.columns:
        return f"Error: column '{value_col}' not in dataset"

    freq = freq.lower().strip()
    if freq in ("y", "year", "yearly", "annual"):
        freq = "year"
    elif freq in ("m", "month", "monthly"):
        freq = "month"

    if freq == "year":
        if df[date_col].dtype in ("int32", "int64"):
            group_col = date_col
        else:
            group_col = _safe_parse_dates(df[date_col]).dt.year
        group_name = "year"
    else:
        group_col = _safe_parse_dates(df[date_col]).dt.to_period("M")
        group_name = "month"

    if isinstance(group_col, str):
        grouped = df.groupby(group_col)[value_col].agg(agg_func)
    else:
        grouped = df.assign(_period=group_col).groupby(
            "_period"
        )[value_col].agg(agg_func)

    grouped = grouped.sort_index()

    result_lines = [f"{group_name} | {value_col}_{agg_func} | pct_change"]
    result_lines.append("-" * 40)

    values = list(grouped.items())
    for i, (period, val) in enumerate(values):
        if i == 0:
            pct = "—"
        else:
            prev = values[i - 1][1]
            if prev != 0:
                pct = f"{((val - prev) / abs(prev)) * 100:+.1f}%"
            else:
                pct = "—"
        result_lines.append(f"{period} | {val:.4f} | {pct}")

    first_val = values[0][1] if values else 0
    last_val = values[-1][1] if values else 0
    if first_val != 0:
        overall_change = ((last_val - first_val) / abs(first_val)) * 100
        result_lines.append(
            f"\nOverall change: {overall_change:+.1f}% "
            f"({first_val:.4f} → {last_val:.4f})"
        )

    n_total = len(df)
    result_lines.append(f"Total records: {n_total}")

    if new_name and values:
        trend_df = pd.DataFrame(values, columns=[group_name, f"{value_col}_{agg_func}"])
        _DATASETS[new_name] = trend_df
        result_lines.append(
            f"(Saved as dataset '{new_name}': {len(trend_df)} rows, "
            f"columns={list(trend_df.columns)})"
        )

    return "\n".join(result_lines)


def cross_tabulate(
    dataset: str,
    row_var: str,
    col_var: str,
    metric: str = "count",
    value_col: str | None = None,
    top_n: int = 10,
    new_name: str | None = None,
) -> str:
    """Cross-tabulation with optional chi-square test.

    Args:
        dataset: Name of a loaded dataset.
        row_var: Row variable.
        col_var: Column variable.
        metric: "count", "mean", "rate" (of value_col).
        value_col: Column for mean/rate calculations.
        top_n: Max categories per variable.

    Returns:
        Cross-tab table with optional chi-square p-value.
    """
    df = get_dataset(dataset)

    for var in [row_var, col_var]:
        if var not in df.columns:
            return f"Error: column '{var}' not in dataset"

    if df[row_var].nunique() > top_n:
        top_cats = df[row_var].value_counts().head(top_n).index
        df = df[df[row_var].isin(top_cats)]

    if df[col_var].nunique() > top_n:
        top_cats = df[col_var].value_counts().head(top_n).index
        df = df[df[col_var].isin(top_cats)]

    if metric == "count":
        ct = pd.crosstab(df[row_var], df[col_var])
    elif metric in ("mean", "rate") and value_col:
        if value_col not in df.columns:
            return f"Error: column '{value_col}' not in dataset"
        ct = df.pivot_table(
            values=value_col, index=row_var,
            columns=col_var, aggfunc="mean",
        ).round(4)
    else:
        return "Error: for 'mean'/'rate' metric, provide value_col"

    result = ct.to_string()

    if metric == "count":
        try:
            chi2, p_val, dof, _ = scipy_stats.chi2_contingency(ct.values)
            result += (
                f"\n\nChi-square test: chi2={chi2:.2f}, "
                f"df={dof}, p={p_val:.4f}"
            )
            if p_val < 0.05:
                result += " (statistically significant)"
            else:
                result += " (not significant)"
        except ValueError:
            pass

    if new_name:
        from src.agent.tools.data import _DATASETS
        saved_df = ct.reset_index()
        _DATASETS[new_name] = saved_df
        result += (
            f"\n(Saved as dataset '{new_name}': "
            f"columns={list(saved_df.columns)})"
        )

    return result


def statistical_test(
    dataset: str,
    test_type: str,
    group_col: str,
    value_col: str,
    groups: list[str] | None = None,
) -> str:
    """Run a statistical test.

    Args:
        dataset: Name of a loaded dataset.
        test_type: "ttest", "mannwhitney", "chi2", "anova", "kruskal".
        group_col: Column defining groups.
        value_col: Column with values to test.
        groups: Specific group values to compare (default: all).

    Returns:
        Test results with statistic, p-value, and interpretation.
    """
    df = get_dataset(dataset)

    if not group_col or not value_col:
        return (
            f"Error: group_col and value_col are required. "
            f"Available columns: {list(df.columns)}"
        )

    for col in [group_col, value_col]:
        if col not in df.columns:
            return f"Error: column '{col}' not in dataset"

    if groups:
        df = df[df[group_col].isin(groups)]

    group_values = df[group_col].unique()

    if test_type in ("ttest", "mannwhitney") and len(group_values) != 2:
        return (
            f"Error: {test_type} requires exactly 2 groups, "
            f"found {len(group_values)}: {list(group_values)}"
        )

    group_data = [
        df[df[group_col] == g][value_col].dropna()
        for g in sorted(group_values)
    ]

    result_lines = [f"Test: {test_type}"]
    result_lines.append(f"Groups: {sorted(group_values)}")
    for g, data in zip(sorted(group_values), group_data):
        result_lines.append(
            f"  {g}: n={len(data)}, mean={data.mean():.4f}, "
            f"std={data.std():.4f}"
        )

    if test_type == "ttest":
        stat, p = scipy_stats.ttest_ind(*group_data, equal_var=False)
        result_lines.append(f"t-statistic: {stat:.4f}, p-value: {p:.6f}")
    elif test_type == "mannwhitney":
        stat, p = scipy_stats.mannwhitneyu(*group_data, alternative="two-sided")
        result_lines.append(f"U-statistic: {stat:.1f}, p-value: {p:.6f}")
    elif test_type == "anova":
        stat, p = scipy_stats.f_oneway(*group_data)
        result_lines.append(f"F-statistic: {stat:.4f}, p-value: {p:.6f}")
    elif test_type == "kruskal":
        stat, p = scipy_stats.kruskal(*group_data)
        result_lines.append(f"H-statistic: {stat:.4f}, p-value: {p:.6f}")
    elif test_type == "chi2":
        ct = pd.crosstab(df[group_col], df[value_col])
        stat, p, dof, _ = scipy_stats.chi2_contingency(ct.values)
        result_lines.append(
            f"Chi2: {stat:.2f}, df={dof}, p-value: {p:.6f}"
        )
    else:
        return f"Error: unknown test type '{test_type}'"

    if p < 0.001:
        result_lines.append("Interpretation: Highly significant (p < 0.001)")
    elif p < 0.05:
        result_lines.append(f"Interpretation: Significant (p = {p:.4f})")
    else:
        result_lines.append(
            f"Interpretation: Not significant (p = {p:.4f})"
        )

    return "\n".join(result_lines)


def logistic_regression(
    dataset: str,
    target: str,
    features: list[str],
) -> str:
    """Fit a logistic regression and return odds ratios.

    Args:
        dataset: Name of a loaded dataset.
        target: Binary target column.
        features: List of feature columns.

    Returns:
        Model summary with coefficients, odds ratios, and metrics.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import (
        accuracy_score,
        roc_auc_score,
    )
    from sklearn.preprocessing import StandardScaler

    df = get_dataset(dataset)

    if target not in df.columns:
        return f"Error: target '{target}' not in dataset"

    available_features = [f for f in features if f in df.columns]
    missing = [f for f in features if f not in df.columns]

    if not available_features:
        return "Error: no valid features found in dataset"

    model_df = df[available_features + [target]].dropna()
    features_matrix = model_df[available_features].values
    y = model_df[target].values

    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features_matrix)

    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(features_scaled, y)

    y_pred = model.predict(features_scaled)
    y_prob = model.predict_proba(features_scaled)[:, 1]

    result_lines = [
        f"Logistic Regression: {target} ~ {' + '.join(available_features)}"
    ]
    if missing:
        result_lines.append(f"Missing features (skipped): {missing}")

    result_lines.append(f"\nSample size: {len(model_df)}")
    result_lines.append(f"Accuracy: {accuracy_score(y, y_pred):.4f}")

    try:
        auc = roc_auc_score(y, y_prob)
        result_lines.append(f"AUC-ROC: {auc:.4f}")
    except ValueError:
        pass

    result_lines.append("\nFeature coefficients and odds ratios:")
    result_lines.append(f"{'Feature':<30} {'Coef':>8} {'OR':>8} {'Impact'}")
    result_lines.append("-" * 65)

    for feat, coef in sorted(
        zip(available_features, model.coef_[0]),
        key=lambda x: abs(x[1]),
        reverse=True,
    ):
        odds_ratio = np.exp(coef)
        direction = "increases risk" if coef > 0 else "decreases risk"
        result_lines.append(
            f"{feat:<30} {coef:>8.4f} {odds_ratio:>8.4f} {direction}"
        )

    return "\n".join(result_lines)

"""Data loading and inspection tools.

These tools handle parquet I/O and dataset description so the LLM
doesn't need to write pandas loading code.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

_DATASETS: dict[str, pd.DataFrame] = {}


def reset_datasets() -> None:
    """Clear all loaded datasets (useful for testing)."""
    _DATASETS.clear()


def list_datasets() -> str:
    """List all loaded datasets with shapes and column names."""
    if not _DATASETS:
        return "No datasets loaded."
    lines = []
    for name, df in _DATASETS.items():
        cols = list(df.columns)
        lines.append(
            f"- **{name}**: {len(df):,} rows, {len(cols)} columns\n"
            f"  Columns: {cols}"
        )
    return "\n".join(lines)


def get_dataset(name: str) -> pd.DataFrame:
    """Retrieve a loaded dataset by name. Raises KeyError if not found."""
    if name not in _DATASETS:
        available = ", ".join(_DATASETS.keys()) or "none"
        raise KeyError(
            f"Dataset '{name}' not found. Available: {available}"
        )
    return _DATASETS[name]


def _find_similar_files(target: str) -> list[str]:
    """Find parquet files on disk that fuzzy-match the target path."""
    target_path = Path(target)
    stem = target_path.stem.lower()

    search_dirs = [Path("."), Path("data"), Path("experiments")]
    suggestions: list[str] = []

    for base in search_dirs:
        if not base.exists():
            continue
        for candidate in base.rglob("*.parquet"):
            if stem in candidate.stem.lower() or candidate.stem.lower() in stem:
                suggestions.append(str(candidate))
            if len(suggestions) >= 5:
                break

    return suggestions


def load_dataset(
    name: str,
    path: str,
    filters: dict[str, str | list] | None = None,
) -> str:
    """Load a parquet file as a named dataset.

    Args:
        name: Dataset identifier (e.g. "sih", "cnes").
        path: Path to .parquet file.
        filters: Optional column filters like {"DIAG_PRINC": "J96"}.

    Returns:
        Summary string with shape, columns, and basic stats.
    """
    file_path = Path(path)
    if not file_path.exists():
        suggestions = _find_similar_files(path)
        hint = ""
        if suggestions:
            hint = "\n  Similar files: " + ", ".join(suggestions[:3])
        available = ", ".join(sorted(_DATASETS.keys())) or "none"
        return (
            f"Error: file not found: {path}{hint}\n"
            f"  Already loaded datasets: {available}"
        )

    df = pd.read_parquet(file_path)

    if filters:
        for col, val in filters.items():
            if col not in df.columns:
                continue
            if isinstance(val, list):
                df = df[df[col].isin(val)]
            else:
                df = df[df[col].astype(str).str.startswith(str(val))]

    _DATASETS[name] = df

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    stats_lines = []
    for col in numeric_cols[:8]:
        stats_lines.append(
            f"  {col}: mean={df[col].mean():.2f}, "
            f"min={df[col].min()}, max={df[col].max()}"
        )

    return (
        f"Loaded '{name}' from {file_path.name}: "
        f"{len(df)} rows, {len(df.columns)} columns\n"
        f"Columns: {list(df.columns)}\n"
        f"Numeric stats:\n" + "\n".join(stats_lines)
    )


def describe_columns(
    dataset: str,
    columns: list[str] | None = None,
) -> str:
    """Describe columns of a loaded dataset.

    Returns value counts for categorical columns, and summary stats
    for numeric columns.
    """
    df = get_dataset(dataset)
    cols = columns or list(df.columns)

    parts = []
    for col in cols:
        if col not in df.columns:
            parts.append(f"{col}: NOT FOUND in dataset")
            continue

        series = df[col]
        missing = series.isna().sum()
        missing_pct = missing / len(df) * 100

        if series.dtype in ("object", "category", "bool"):
            vc = series.value_counts().head(10)
            vc_str = ", ".join(f"{k}={v}" for k, v in vc.items())
            parts.append(
                f"{col} (categorical, {missing_pct:.1f}% missing): "
                f"top values: {vc_str}"
            )
        elif hasattr(series.dtype, "tz") or "datetime" in str(series.dtype):
            parts.append(
                f"{col} (datetime, {missing_pct:.1f}% missing): "
                f"min={series.min()}, max={series.max()}"
            )
        elif "timedelta" in str(series.dtype):
            parts.append(
                f"{col} (timedelta, {missing_pct:.1f}% missing): "
                f"min={series.min()}, max={series.max()}"
            )
        else:
            try:
                parts.append(
                    f"{col} (numeric, {missing_pct:.1f}% missing): "
                    f"mean={series.mean():.3f}, std={series.std():.3f}, "
                    f"min={series.min()}, max={series.max()}"
                )
            except (TypeError, ValueError):
                parts.append(
                    f"{col} ({series.dtype}, {missing_pct:.1f}% missing)"
                )

    return "\n".join(parts)


def _parse_string_condition(cond_str: str) -> dict[str, str | list]:
    """Parse a string condition like 'COL == "val"' into a dict."""
    import re as _re

    cond_str = cond_str.strip()

    for op in ("==", "!=", ">=", "<=", ">", "<"):
        if op in cond_str:
            parts = cond_str.split(op, 1)
            col = parts[0].strip().strip('"').strip("'")
            val = parts[1].strip().strip('"').strip("'")
            if op == "==" or op == "!=":
                return {col: val}
            return {col: f"{op}{val}"}

    m = _re.match(r'(\w+)\.str\.startswith\(["\'](\w+)["\']\)', cond_str)
    if m:
        return {m.group(1): m.group(2)}

    m = _re.match(r'(\w+)\.isin\(\[(.+)\]\)', cond_str)
    if m:
        values = [v.strip().strip('"').strip("'") for v in m.group(2).split(",")]
        return {m.group(1): values}

    return {}


def filter_dataset(
    dataset: str,
    conditions: dict[str, str | int | float | list] | str,
    new_name: str | None = None,
) -> str:
    """Filter a dataset and optionally save as a new named dataset.

    Conditions can be:
        {"column": value}           — equality filter
        {"column": [v1, v2]}        — isin filter
        {"column": ">50"}           — comparison (supports >, <, >=, <=)
        "COL == 'val'"              — string expression (auto-parsed)
    """
    df = get_dataset(dataset)
    original_len = len(df)

    if isinstance(conditions, str):
        conditions = _parse_string_condition(conditions)
        if not conditions:
            save_name = new_name or f"{dataset}_filtered"
            _DATASETS[save_name] = df
            return (
                f"Warning: could not parse condition string. "
                f"Saved unchanged as '{save_name}' ({len(df)} rows)"
            )

    for col, val in conditions.items():
        if col not in df.columns:
            continue
        if isinstance(val, dict):
            if "startswith" in val:
                df = df[df[col].astype(str).str.startswith(str(val["startswith"]))]
            elif "contains" in val:
                df = df[df[col].astype(str).str.contains(str(val["contains"]), na=False)]
            elif "isin" in val:
                df = df[df[col].isin(val["isin"])]
        elif isinstance(val, list):
            df = df[df[col].isin(val)]
        elif isinstance(val, str) and val[:1] in (">", "<"):
            op = val[:2] if val[:2] in (">=", "<=") else val[:1]
            num = float(val[len(op):])
            if op == ">":
                df = df[df[col] > num]
            elif op == "<":
                df = df[df[col] < num]
            elif op == ">=":
                df = df[df[col] >= num]
            elif op == "<=":
                df = df[df[col] <= num]
        elif isinstance(val, str) and val.endswith("*"):
            prefix = val[:-1]
            df = df[df[col].astype(str).str.startswith(prefix)]
        else:
            df = df[df[col] == val]

    save_name = new_name or f"{dataset}_filtered"

    if len(df) == 0:
        original_df = get_dataset(dataset)
        sample_vals = {}
        for col in conditions:
            if col in original_df.columns:
                unique = original_df[col].dropna().unique()[:8]
                sample_vals[col] = [str(v) for v in unique]
        hint = ""
        if sample_vals:
            hint = " Sample values: " + "; ".join(
                f"{c}={vs}" for c, vs in sample_vals.items()
            )
        return (
            f"Error: filter produced 0 rows from '{dataset}' "
            f"({original_len} rows).{hint} "
            f"For ICD codes use prefix matching: "
            f'{{\"col\": \"J96*\"}} or {{\"col\": {{\"startswith\": \"J96\"}}}}'
        )

    _DATASETS[save_name] = df

    return (
        f"Filtered '{dataset}': {original_len} → {len(df)} rows "
        f"(saved as '{save_name}')"
    )

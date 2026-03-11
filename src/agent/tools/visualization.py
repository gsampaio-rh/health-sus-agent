"""Visualization tools — chart creation from datasets.

Charts are saved to the output directory as PNG files. The agent
receives a confirmation string with the file path.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from src.agent.tools.data import get_dataset

matplotlib.use("Agg")

_OUTPUT_DIR = Path("outputs/plots")


def set_output_dir(path: str | Path) -> None:
    global _OUTPUT_DIR
    _OUTPUT_DIR = Path(path)
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_chart(
    chart_type: str,
    dataset: str,
    x: str,
    y: str,
    title: str,
    hue: str | None = None,
    agg_func: str = "mean",
    top_n: int = 15,
    filename: str | None = None,
) -> str:
    """Create a chart from a dataset and save as PNG.

    Args:
        chart_type: "bar", "line", "heatmap", "scatter".
        dataset: Name of a loaded dataset.
        x: X-axis column.
        y: Y-axis column.
        title: Chart title.
        hue: Optional grouping column.
        agg_func: How to aggregate y ("mean", "sum", "count").
        top_n: Max categories for bar charts.
        filename: Output filename (auto-generated if not provided).

    Returns:
        Path to saved chart file.
    """
    df = get_dataset(dataset)

    for col in [x, y]:
        if col not in df.columns:
            return f"Error: column '{col}' not in dataset"

    if hue and hue not in df.columns:
        return f"Error: hue column '{hue}' not in dataset"

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    try:
        if chart_type == "bar":
            _bar_chart(df, x, y, agg_func, hue, top_n, ax)
        elif chart_type == "line":
            _line_chart(df, x, y, agg_func, hue, ax)
        elif chart_type == "heatmap":
            _heatmap(df, x, y, agg_func, ax)
        elif chart_type == "scatter":
            ax.scatter(df[x], df[y], alpha=0.3, s=10)
            ax.set_xlabel(x)
            ax.set_ylabel(y)
        else:
            plt.close(fig)
            return f"Error: unknown chart type '{chart_type}'"

        ax.set_title(title)
        plt.tight_layout()

        fname = filename or f"{dataset}_{x}_{y}_{chart_type}.png"
        if not fname.endswith(".png"):
            fname += ".png"
        out_path = _OUTPUT_DIR / fname
        fig.savefig(out_path, dpi=150)
        plt.close(fig)

        return f"Chart saved: {out_path}"

    except Exception as e:
        plt.close(fig)
        return f"Error creating chart: {e}"


def _bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    agg_func: str,
    hue: str | None,
    top_n: int,
    ax: plt.Axes,
) -> None:
    if hue:
        pivot = df.pivot_table(
            values=y, index=x, columns=hue, aggfunc=agg_func
        )
        if len(pivot) > top_n:
            totals = pivot.sum(axis=1).nlargest(top_n).index
            pivot = pivot.loc[totals]
        pivot.plot(kind="bar", ax=ax)
        ax.legend(title=hue, bbox_to_anchor=(1.05, 1))
    else:
        grouped = df.groupby(x)[y].agg(agg_func).nlargest(top_n)
        grouped.plot(kind="bar", ax=ax)
    ax.set_xlabel(x)
    ax.set_ylabel(f"{y} ({agg_func})")
    ax.tick_params(axis="x", rotation=45)


def _line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    agg_func: str,
    hue: str | None,
    ax: plt.Axes,
) -> None:
    if hue:
        pivot = df.pivot_table(
            values=y, index=x, columns=hue, aggfunc=agg_func
        )
        pivot.plot(kind="line", ax=ax, marker="o")
        ax.legend(title=hue, bbox_to_anchor=(1.05, 1))
    else:
        grouped = df.groupby(x)[y].agg(agg_func).sort_index()
        grouped.plot(kind="line", ax=ax, marker="o")
    ax.set_xlabel(x)
    ax.set_ylabel(f"{y} ({agg_func})")


def _heatmap(
    df: pd.DataFrame,
    x: str,
    y: str,
    agg_func: str,
    ax: plt.Axes,
) -> None:
    pivot = df.pivot_table(values=y, index=x, aggfunc=agg_func)
    if pivot.shape[1] == 1:
        pivot = pivot.T
    im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    plt.colorbar(im, ax=ax)

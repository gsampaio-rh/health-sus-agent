"""Analysis Engine — sandboxed Python REPL with execution trace.

Provides ReplSandbox (exec + capture) and AnalysisEngine (sandbox + trace
logging). The REPL namespace persists across calls so dataframes, models,
and variables survive between analysis steps.
"""

from __future__ import annotations

import io
import json
import signal
import sys
import time
import traceback
from contextlib import contextmanager
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

from src.agent.state import CodeExecution

matplotlib.use("Agg")


class ReplTimeoutError(Exception):
    pass


@contextmanager
def _timeout(seconds: int):
    """Unix signal-based timeout. Falls through silently on non-Unix."""
    if seconds <= 0 or not hasattr(signal, "SIGALRM"):
        yield
        return

    def _handler(signum, frame):
        raise ReplTimeoutError(f"Code execution exceeded {seconds}s timeout")

    old_handler = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class ReplSandbox:
    """Sandboxed Python REPL with persistent namespace and output capture."""

    def __init__(
        self,
        output_dir: str | Path = "outputs",
        timeout_seconds: int = 120,
        max_output_chars: int = 50_000,
    ):
        self.output_dir = Path(output_dir)
        self.plot_dir = self.output_dir / "plots"
        self.metrics_dir = self.output_dir / "metrics"
        self.timeout_seconds = timeout_seconds
        self.max_output_chars = max_output_chars
        self._artifacts: list[str] = []

        self.plot_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        self.namespace: dict = self._build_namespace()

    def _build_namespace(self) -> dict:
        """Pre-load the REPL namespace with common libraries and helpers."""
        ns: dict = {
            "pd": pd,
            "np": np,
            "plt": plt,
            "sns": sns,
            "stats": stats,
            "Path": Path,
            "save_plot": self._save_plot,
            "save_metrics": self._save_metrics,
            "__builtins__": __builtins__,
        }
        sns.set_theme(style="whitegrid", palette="deep", font_scale=1.1)
        plt.rcParams.update({
            "figure.dpi": 120,
            "savefig.dpi": 150,
            "savefig.bbox": "tight",
            "figure.figsize": (12, 6),
        })
        return ns

    def _save_plot(self, fig: plt.Figure, name: str) -> str:
        """Save a matplotlib figure and track it as an artifact."""
        path = self.plot_dir / f"{name}.png"
        fig.savefig(path, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        artifact = str(path)
        self._artifacts.append(artifact)
        return artifact

    def _save_metrics(self, data: dict, name: str) -> str:
        """Save a metrics dict as JSON and track it as an artifact."""
        path = self.metrics_dir / f"{name}.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        artifact = str(path)
        self._artifacts.append(artifact)
        return artifact

    def execute(self, code: str) -> tuple[str, str | None, list[str]]:
        """Execute code in the sandbox.

        Returns (stdout, error_or_none, artifact_paths).
        """
        self._artifacts = []
        stdout_capture = io.StringIO()
        error: str | None = None

        old_stdout = sys.stdout
        try:
            sys.stdout = stdout_capture
            with _timeout(self.timeout_seconds):
                exec(code, self.namespace)  # noqa: S102
        except ReplTimeoutError as e:
            error = str(e)
        except Exception:
            error = traceback.format_exc()
        finally:
            sys.stdout = old_stdout

        output = stdout_capture.getvalue()
        if len(output) > self.max_output_chars:
            output = (
                output[: self.max_output_chars]
                + f"\n... truncated at {self.max_output_chars} chars"
            )

        return output, error, list(self._artifacts)


class AnalysisEngine:
    """REPL sandbox + structured execution trace logging."""

    def __init__(
        self,
        output_dir: str | Path = "outputs",
        timeout_seconds: int = 120,
        max_output_chars: int = 50_000,
    ):
        self.sandbox = ReplSandbox(
            output_dir=output_dir,
            timeout_seconds=timeout_seconds,
            max_output_chars=max_output_chars,
        )
        self.trace: list[CodeExecution] = []

    @property
    def namespace(self) -> dict:
        return self.sandbox.namespace

    def execute(self, code: str, node: str = "unnamed") -> CodeExecution:
        """Execute code, capture results, and append to the trace."""
        start = time.perf_counter_ns()
        output, error, artifacts = self.sandbox.execute(code)
        duration_ms = int((time.perf_counter_ns() - start) / 1_000_000)

        entry = CodeExecution(
            node=node,
            code=code,
            output=output,
            error=error,
            artifacts=artifacts,
            duration_ms=duration_ms,
        )
        self.trace.append(entry)
        return entry

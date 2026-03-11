"""Tracer — structured logging for investigation runs.

Writes a per-run log file and a JSON trace to the logs/ directory.
Each run gets a timestamped folder with:
  - run.log      — human-readable log with timestamps
  - trace.json   — machine-readable full execution trace
  - plan.json    — the investigation plan
  - summary.json — final results summary
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from loguru import logger


class InvestigationTracer:
    """Manages structured logging for a single investigation run."""

    def __init__(self, logs_dir: str | Path = "logs"):
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = Path(logs_dir) / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

        self.log_path = self.run_dir / "run.log"
        self.events: list[dict] = []

        self._setup_logger()

    def _setup_logger(self) -> None:
        """Configure loguru to write to both stderr and the run log file."""
        logger.remove()
        log_format = (
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
            "{message}"
        )
        logger.add(sys.stderr, format=log_format, level="INFO")
        logger.add(
            str(self.log_path),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            level="DEBUG",
        )

    def log_event(
        self,
        event_type: str,
        data: dict | None = None,
    ) -> None:
        """Record a structured event to the trace."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            **(data or {}),
        }
        self.events.append(event)

    def save_plan(self, plan_data: dict) -> None:
        """Save the investigation plan as JSON."""
        path = self.run_dir / "plan.json"
        with open(path, "w") as f:
            json.dump(plan_data, f, indent=2, default=str)

    def save_step_result(
        self,
        step_index: int,
        step_name: str,
        decision: str,
        summary: str,
        duration_ms: int,
        tool_calls: list[dict] | None = None,
        artifacts: list[str] | None = None,
        llm_reasoning: str = "",
        code: str = "",
        output: str = "",
        error: str | None = None,
    ) -> None:
        """Record a completed step to the trace."""
        self.log_event("step_completed", {
            "step_index": step_index,
            "step_name": step_name,
            "decision": decision,
            "summary": summary[:300],
            "n_tool_calls": len(tool_calls or []),
            "n_artifacts": len(artifacts or []),
            "duration_ms": duration_ms,
        })

        step_data = {
            "step_index": step_index,
            "step_name": step_name,
            "decision": decision,
            "summary": summary,
            "duration_ms": duration_ms,
            "artifacts": artifacts or [],
        }

        if tool_calls:
            step_data["tool_calls"] = tool_calls
        if llm_reasoning:
            step_data["llm_reasoning"] = llm_reasoning
        if code:
            step_data["code"] = code
        if output:
            step_data["output"] = output[:10000]
        if error:
            step_data["error"] = error

        step_file = self.run_dir / f"step_{step_index:02d}_{step_name}.json"
        with open(step_file, "w") as f:
            json.dump(step_data, f, indent=2, default=str)

    def save_summary(self, summary_data: dict) -> None:
        """Save the final investigation summary."""
        path = self.run_dir / "summary.json"
        with open(path, "w") as f:
            json.dump(summary_data, f, indent=2, default=str)

        # Also save the full event trace
        trace_path = self.run_dir / "trace.json"
        with open(trace_path, "w") as f:
            json.dump(self.events, f, indent=2, default=str)

        logger.info(f"Run logs saved to {self.run_dir}/")

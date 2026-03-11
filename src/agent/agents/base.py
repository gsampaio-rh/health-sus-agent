"""BaseAgent — shared reasoning framework for all agents.

Every agent follows the Goal-Plan-Act-Observe-Reflect (GPAOR) loop.
Each loop iteration fills a structured scratchpad that becomes part
of the trace and is visible to the Critic.
"""

from __future__ import annotations

import json
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from loguru import logger

from src.agent.context import InvestigationContext
from src.agent.skill import load_skill
from src.agent.state import StepTrace, ToolCall
from src.agent.tools import analysis as analysis_tools
from src.agent.tools import data as data_tools
from src.agent.tools import findings as findings_tools
from src.agent.tools import visualization as viz_tools

TOOL_REGISTRY = {
    "load_dataset": data_tools.load_dataset,
    "list_datasets": data_tools.list_datasets,
    "describe_columns": data_tools.describe_columns,
    "filter_dataset": data_tools.filter_dataset,
    "aggregate": analysis_tools.aggregate,
    "time_series": analysis_tools.time_series,
    "cross_tabulate": analysis_tools.cross_tabulate,
    "statistical_test": analysis_tools.statistical_test,
    "logistic_regression": analysis_tools.logistic_regression,
    "create_chart": viz_tools.create_chart,
    "record_finding": findings_tools.record_finding,
    "get_findings_summary": findings_tools.get_findings_summary,
    "add_open_question": findings_tools.add_open_question,
}

TOOL_DESCRIPTIONS: dict[str, str] = {}


def _build_tool_descriptions() -> dict[str, str]:
    return {
        "load_dataset": (
            "Load a parquet file. "
            "Args: name(str), path(str), filters(dict, opt)"
        ),
        "list_datasets": "List loaded datasets. No args needed.",
        "describe_columns": (
            "Describe columns. "
            "Args: dataset(str), columns(list, opt)"
        ),
        "filter_dataset": (
            "Filter & save as new dataset. "
            "Args: dataset(str), conditions(dict), new_name(str, opt)"
        ),
        "aggregate": (
            "Group-by aggregation, optionally save result. "
            "Args: dataset(str), group_by(list), "
            'metrics(dict: name->"col:func"), '
            "sort_by(str, opt), new_name(str, opt)"
        ),
        "time_series": (
            "Temporal trends. "
            "Args: dataset(str), date_col(str), value_col(str), "
            "freq(year/month), agg_func(mean/sum/count), "
            "new_name(str, opt)"
        ),
        "cross_tabulate": (
            "Cross-tab with chi2. "
            "Args: dataset(str), row_var(str), col_var(str), "
            "metric(count/mean), value_col(str, opt), "
            "new_name(str, opt)"
        ),
        "statistical_test": (
            "Statistical test. "
            "Args: dataset(str), "
            "test_type(ttest/mannwhitney/chi2/anova/kruskal), "
            "group_col(str), value_col(str), groups(list, opt)"
        ),
        "logistic_regression": (
            "Logistic regression. "
            "Args: dataset(str), target(str), features(list[str])"
        ),
        "create_chart": (
            "Create chart from a saved dataset. "
            "Args: chart_type(bar/line/heatmap/scatter), "
            "dataset(str), x(str), y(str), title(str), "
            "hue(str, opt), agg_func(str, opt), filename(str, opt)"
        ),
        "record_finding": (
            "Record a finding. "
            "Args: finding_id(str), statement(str), "
            "evidence(str), so_what(str), "
            "confidence(high/medium/low)"
        ),
        "get_findings_summary": "Get all findings summary. No args.",
        "add_open_question": (
            "Add open question. Args: question(str)"
        ),
    }


TOOL_DESCRIPTIONS = _build_tool_descriptions()


@dataclass
class Scratchpad:
    """Structured thinking space for an agent."""

    goal: str = ""
    plan: list[str] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    hypotheses: list[str] = field(default_factory=list)
    evidence_for: list[str] = field(default_factory=list)
    evidence_against: list[str] = field(default_factory=list)
    confounders: list[str] = field(default_factory=list)
    conclusions: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        parts = []
        if self.goal:
            parts.append(f"## Goal\n{self.goal}")
        if self.plan:
            parts.append("## Plan\n" + "\n".join(f"- {p}" for p in self.plan))
        if self.hypotheses:
            parts.append("## Hypotheses\n" + "\n".join(f"- {h}" for h in self.hypotheses))
        if self.evidence_for:
            parts.append("## Evidence For\n" + "\n".join(f"- {e}" for e in self.evidence_for))
        if self.evidence_against:
            items = "\n".join(f"- {e}" for e in self.evidence_against)
            parts.append(f"## Evidence Against\n{items}")
        if self.confounders:
            items = "\n".join(f"- {c}" for c in self.confounders)
            parts.append(f"## Confounders Considered\n{items}")
        if self.conclusions:
            parts.append("## Conclusions\n" + "\n".join(f"- {c}" for c in self.conclusions))
        if self.open_questions:
            parts.append("## Open Questions\n" + "\n".join(f"- {q}" for q in self.open_questions))
        if self.observations:
            parts.append("## Observations\n" + "\n".join(f"- {o[:200]}" for o in self.observations))
        return "\n\n".join(parts)


@dataclass
class AgentResult:
    """Output of an agent's run."""

    agent_name: str
    report_path: str = ""
    report_content: str = ""
    scratchpad: Scratchpad = field(default_factory=Scratchpad)
    trace: StepTrace = field(default_factory=lambda: StepTrace(step_name=""))
    duration_ms: int = 0
    error: str | None = None


def parse_tool_calls(raw: str) -> list[dict]:
    """Parse LLM output into a list of tool call dicts."""
    text = raw.strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if "```" in text:
            text = text[:text.rfind("```")]
        text = text.strip()

    if "[" in text:
        start = text.find("[")
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "[":
                depth += 1
            elif text[i] == "]":
                depth -= 1
                if depth == 0:
                    text = text[start:i + 1]
                    break
    elif "{" in text:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end + 1]

    text = text.strip()
    if not text:
        return []

    def _sanitize(m: re.Match) -> str:
        s = m.group(0)
        inner = s[1:-1]
        inner = inner.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        return '"' + inner + '"'

    text = re.sub(r'"(?:[^"\\]|\\.)*"', _sanitize, text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []

    if isinstance(data, list):
        return [_normalize_tool_dict(d) for d in data if isinstance(d, dict)]
    if isinstance(data, dict):
        if "tool_calls" in data:
            return [_normalize_tool_dict(d) for d in data["tool_calls"] if isinstance(d, dict)]
        if "tool" in data or "name" in data:
            return [_normalize_tool_dict(data)]
    return []


def _normalize_tool_dict(d: dict) -> dict:
    """Normalize tool call dicts that may use different key names.

    Handles: {"tool", "args"}, {"name", "arguments"},
    {"name", "parameters"}, {"function", "arguments"}, etc.
    """
    tool = d.get("tool") or d.get("name") or d.get("function") or ""
    args = d.get("args") or d.get("arguments") or d.get("parameters") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except (json.JSONDecodeError, ValueError):
            args = {}
    return {"tool": tool, "args": args if isinstance(args, dict) else {}}


_DATASET_TOOLS = {
    "aggregate", "time_series", "cross_tabulate", "filter_dataset",
    "describe_columns", "create_chart", "statistical_test",
    "logistic_regression",
}

_COLUMN_PARAMS = {
    "group_by", "date_col", "value_col", "x", "y", "row_var", "col_var",
}


def _pre_validate(name: str, args: dict) -> str | None:
    """Return an actionable error if dataset/columns don't exist, else None."""
    from src.agent.tools.data import _DATASETS

    if name not in _DATASET_TOOLS:
        return None

    ds_name = args.get("dataset", "")
    if not ds_name or ds_name not in _DATASETS:
        if ds_name:
            available = ", ".join(sorted(_DATASETS.keys())) or "none"
            return (
                f"Dataset '{ds_name}' not found. "
                f"Available datasets: {available}"
            )
        return None

    df = _DATASETS[ds_name]
    cols = set(df.columns)

    bad_cols = []
    for param_name in _COLUMN_PARAMS:
        val = args.get(param_name)
        if val is None:
            continue
        check_list = val if isinstance(val, list) else [val]
        for col in check_list:
            if isinstance(col, str) and col not in cols:
                bad_cols.append(col)

    if bad_cols:
        return (
            f"Column(s) {bad_cols} not in dataset '{ds_name}'. "
            f"Available columns: {sorted(str(c) for c in cols)}"
        )

    return None


def _enrich_error(error_msg: str, tool_name: str, args: dict) -> str:
    """Add available datasets/columns to error messages so LLM can self-correct."""
    from src.agent.tools.data import _DATASETS

    enriched = error_msg

    if "not found" in error_msg and "Dataset" in error_msg:
        available = ", ".join(sorted(_DATASETS.keys())) or "none"
        enriched += f"\n  Available datasets: {available}"

    elif "not in dataset" in error_msg or "not in index" in error_msg:
        ds_name = args.get("dataset", "")
        if ds_name and ds_name in _DATASETS:
            cols = list(_DATASETS[ds_name].columns)
            enriched += f"\n  Columns in '{ds_name}': {cols}"

    return enriched


def execute_tool(name: str, args: dict) -> ToolCall:
    """Execute a single tool call with pre-validation."""
    start = time.perf_counter()

    if name not in TOOL_REGISTRY:
        return ToolCall(tool_name=name, arguments=args, error=f"Unknown tool: {name}")

    validation_error = _pre_validate(name, args)
    if validation_error:
        duration = int((time.perf_counter() - start) * 1000)
        return ToolCall(
            tool_name=name, arguments=args,
            error=validation_error, duration_ms=duration,
        )

    try:
        result = TOOL_REGISTRY[name](**args)
        duration = int((time.perf_counter() - start) * 1000)

        if isinstance(result, str) and result.startswith("Error:"):
            error_text = result[len("Error:"):].strip()
            enriched = _enrich_error(error_text, name, args)
            return ToolCall(
                tool_name=name, arguments=args,
                error=enriched, duration_ms=duration,
            )

        artifacts = []
        if isinstance(result, str) and "Chart saved:" in result:
            artifacts.append(result.replace("Chart saved: ", "").strip())
        return ToolCall(
            tool_name=name, arguments=args, result=str(result),
            artifacts=artifacts, duration_ms=duration,
        )
    except Exception as e:
        duration = int((time.perf_counter() - start) * 1000)
        error_msg = f"{type(e).__name__}: {e}"
        enriched = _enrich_error(error_msg, name, args)
        return ToolCall(
            tool_name=name, arguments=args,
            error=enriched, duration_ms=duration,
        )


_FORMAT_EXAMPLE = """
## JSON format (REQUIRED)

```json
[
  {"tool": "aggregate", "args": {"dataset": "sih", "group_by": ["year"], \
"metrics": {"count": "MORTE:count", "rate": "MORTE:mean"}, \
"new_name": "yearly_stats"}},
  {"tool": "create_chart", "args": {"chart_type": "line", \
"dataset": "yearly_stats", "x": "year", "y": "rate", \
"title": "Mortality Rate", "filename": "01_mortality.png"}},
  {"tool": "record_finding", "args": {"finding_id": "f1", \
"statement": "Mortality rose 6pp", "evidence": "30% to 36%", \
"so_what": "Needs intervention", "confidence": "high"}}
]
```

EVERY tool call MUST have "tool" and "args" keys.
To save results for charting, use new_name in aggregate/time_series.
"""


def build_tools_description() -> str:
    lines = ["## Available tools", ""]
    for name, desc in TOOL_DESCRIPTIONS.items():
        lines.append(f"- **{name}**: {desc}")
    lines.append(_FORMAT_EXAMPLE)
    return "\n".join(lines)


class BaseAgent(ABC):
    """Abstract base for all spine agents.

    Subclasses implement:
        - agent_name: str property
        - skill_names: which skills to load
        - system_prompt(): the system prompt for this agent
        - build_user_prompt(): the user message for the first LLM call
        - process_response(): handle LLM response and decide next action
        - generate_report(): produce the final markdown report
    """

    def __init__(
        self,
        llm: BaseChatModel,
        context: InvestigationContext,
        run_dir: Path,
        max_tool_rounds: int = 5,
    ):
        self.llm = llm
        self.context = context
        self.run_dir = run_dir
        self.max_tool_rounds = max_tool_rounds
        self.scratchpad = Scratchpad()
        self.trace = StepTrace(step_name=self.agent_name)
        self.skill = load_skill(names=self.skill_names)

    @property
    @abstractmethod
    def agent_name(self) -> str:
        ...

    @property
    @abstractmethod
    def skill_names(self) -> list[str]:
        ...

    @abstractmethod
    def system_prompt(self) -> str:
        ...

    @abstractmethod
    def build_user_prompt(self) -> str:
        ...

    @abstractmethod
    def generate_report(self) -> str:
        ...

    def run(self) -> AgentResult:
        """Execute the GPAOR loop and produce a result."""
        start = time.perf_counter()
        logger.info(f"[{self.agent_name}] Starting")

        self.scratchpad.goal = self._get_goal()

        messages: list[BaseMessage] = [
            SystemMessage(content=self.system_prompt()),
            HumanMessage(content=self.build_user_prompt()),
        ]

        for round_num in range(self.max_tool_rounds):
            try:
                response = self.llm.invoke(messages)
                raw = response.content
            except Exception as e:
                logger.error(f"[{self.agent_name}] LLM call failed: {e}")
                self.scratchpad.observations.append(f"LLM error: {e}")
                break

            tool_calls = parse_tool_calls(raw)
            if not tool_calls:
                self.trace.llm_reasoning += raw[:2000]
                logger.debug(f"[{self.agent_name}] Round {round_num + 1}: no tool calls, done")
                break

            logger.debug(f"[{self.agent_name}] Round {round_num + 1}: {len(tool_calls)} tools")

            round_results = []
            for tc_dict in tool_calls:
                tool_name = tc_dict.get("tool", "")
                tool_args = tc_dict.get("args", {})
                if not tool_name:
                    continue

                tc = execute_tool(tool_name, tool_args)
                self.trace.tool_calls.append(tc)
                if tc.artifacts:
                    self.trace.artifacts.extend(tc.artifacts)

                status = "OK" if not tc.error else f"ERR: {tc.error[:80]}"
                logger.debug(f"[{self.agent_name}]   {tool_name}: {status}")

                if tc.error:
                    round_results.append(f"[{tool_name}] Error: {tc.error}")
                else:
                    round_results.append(f"[{tool_name}] {tc.result[:1000]}")
                    self.scratchpad.observations.append(
                        f"{tool_name}: {tc.result[:300]}"
                    )

            results_text = "\n\n".join(round_results)
            messages.append(HumanMessage(
                content=(
                    f"## Results from round {round_num + 1}\n\n{results_text}\n\n"
                    f"What additional tool calls should I make? "
                    f"Respond with [] when done."
                )
            ))

        # Generate report
        report_content = self.generate_report()
        report_path = self._save_report(report_content)

        # Save trace
        self._save_trace()

        duration = int((time.perf_counter() - start) * 1000)
        self.trace.duration_ms = duration

        logger.info(
            f"[{self.agent_name}] Completed in {duration}ms "
            f"({len(self.trace.tool_calls)} tool calls)"
        )

        return AgentResult(
            agent_name=self.agent_name,
            report_path=report_path,
            report_content=report_content,
            scratchpad=self.scratchpad,
            trace=self.trace,
            duration_ms=duration,
        )

    def _get_goal(self) -> str:
        return f"{self.agent_name}: process investigation"

    def _save_report(self, content: str) -> str:
        reports_dir = self.run_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        filename = self._report_filename()
        path = reports_dir / filename
        path.write_text(content, encoding="utf-8")
        return str(path)

    def _save_trace(self) -> None:
        traces_dir = self.run_dir / "traces"
        traces_dir.mkdir(parents=True, exist_ok=True)
        trace_path = traces_dir / f"{self.agent_name}_trace.json"

        trace_data = {
            "agent": self.agent_name,
            "scratchpad": self.scratchpad.to_markdown(),
            "tool_calls": [
                {
                    "tool": tc.tool_name,
                    "args": tc.arguments,
                    "result": tc.result[:500],
                    "error": tc.error,
                    "duration_ms": tc.duration_ms,
                }
                for tc in self.trace.tool_calls
            ],
            "artifacts": self.trace.artifacts,
            "llm_reasoning": self.trace.llm_reasoning[:2000],
            "duration_ms": self.trace.duration_ms,
        }

        with open(trace_path, "w") as f:
            json.dump(trace_data, f, indent=2, ensure_ascii=False, default=str)

    @abstractmethod
    def _report_filename(self) -> str:
        ...

    def _ask_llm(self, system: str, user: str) -> str:
        """Simple single-turn LLM call for report generation."""
        messages = [
            SystemMessage(content=system),
            HumanMessage(content=user),
        ]
        response = self.llm.invoke(messages)
        return response.content

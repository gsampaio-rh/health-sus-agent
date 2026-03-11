"""Investigation tree — generate a markdown tree of the full run.

Produces a hierarchical view from root question → agents → tool calls,
saved as tree.md in the run directory.
"""

from __future__ import annotations

from pathlib import Path

from src.agent.context import InvestigationContext


def _format_duration(ms: int) -> str:
    if ms == 0:
        return "cached"
    if ms < 1000:
        return f"{ms}ms"
    return f"{ms / 1000:.1f}s"


def _tool_line(
    tc: "ToolCall", prefix: str, connector: str,
) -> list[str]:
    """Render one tool call as a tree line."""
    from src.agent.state import ToolCall  # noqa: F811

    status = "x" if tc.error else "✓"
    dur = _format_duration(tc.duration_ms)
    cached = " [cached]" if tc.result and "[cached]" in tc.result else ""

    summary = ""
    if tc.tool_name == "filter_dataset":
        ds = tc.arguments.get("dataset", "")
        new = tc.arguments.get("new_name", "")
        summary = f"{ds} → {new}" if new else ds
    elif tc.tool_name == "aggregate":
        ds = tc.arguments.get("dataset", "")
        new = tc.arguments.get("new_name", "")
        group = tc.arguments.get("group_by", [])
        summary = f"{ds} by {group}" + (f" → {new}" if new else "")
    elif tc.tool_name == "time_series":
        ds = tc.arguments.get("dataset", "")
        col = tc.arguments.get("value_col", "")
        summary = f"{ds}.{col}"
    elif tc.tool_name == "create_chart":
        summary = tc.arguments.get("filename", "")
    elif tc.tool_name == "record_finding":
        stmt = tc.arguments.get("statement", "")
        summary = stmt[:80] + ("…" if len(stmt) > 80 else "")
    elif tc.tool_name == "load_dataset":
        summary = tc.arguments.get("name", "")
    elif tc.tool_name == "describe_columns":
        summary = tc.arguments.get("dataset", "")
    elif tc.tool_name == "statistical_test":
        test = tc.arguments.get("test_type", "")
        summary = f"{test} on {tc.arguments.get('dataset', '')}"
    elif tc.tool_name == "add_open_question":
        q = tc.arguments.get("question", "")
        summary = q[:80] + ("…" if len(q) > 80 else "")
    elif tc.tool_name == "cross_tabulate":
        ds = tc.arguments.get("dataset", "")
        summary = f"{ds} ({tc.arguments.get('row_var', '')} × {tc.arguments.get('col_var', '')})"
    elif tc.tool_name == "logistic_regression":
        summary = tc.arguments.get("dataset", "")
    else:
        summary = ""

    detail = f" — {summary}" if summary else ""
    line = f"{prefix}{connector} [{status}] {tc.tool_name}{detail} ({dur}){cached}"

    lines = [line]
    if tc.error:
        err_short = tc.error[:120].replace("\n", " ")
        lines.append(f"{prefix}{'│' if connector == '├──' else '   '}     ⚠ {err_short}")

    return lines


def generate_tree(
    result: "SpineResult",
    context: InvestigationContext,
) -> str:
    """Build a markdown investigation tree from a completed spine run."""
    lines: list[str] = []

    lines.append("# Investigation Tree")
    lines.append("")
    lines.append(f"**Run:** `{result.run_id}`")
    lines.append(f"**Model:** `{context.model}`")
    lines.append(f"**Duration:** {_format_duration(result.duration_ms)}")
    lines.append("")
    lines.append(f"## {context.question}")
    lines.append("")

    agent_results = list(result.agent_results)
    recovery_results = list(result.recovery_results)

    rq_idx = 0
    for ar in agent_results:
        name = ar.agent_name
        tcs = ar.trace.tool_calls
        errors = sum(1 for tc in tcs if tc.error)
        dur = _format_duration(ar.duration_ms)

        if name == "director":
            rq_count = len(context.research_questions)
            lines.append(f"├── **Phase 1: Director** ({dur})")
            lines.append(f"│   └── Planned {rq_count} research questions")
            for rq in context.research_questions:
                lines.append(f"│       ├── {rq.id}: {rq.title}")
            lines.append("│")

        elif name == "data_agent":
            ds_count = len(context.datasets_loaded)
            cache_hits = sum(1 for tc in tcs if tc.result and "[cached]" in tc.result)
            error_str = f", {errors} errors" if errors else ""
            cache_str = f", {cache_hits} cached" if cache_hits else ""
            lines.append(
                f"├── **Phase 2: DataAgent** — "
                f"{ds_count} datasets, {len(tcs)} tools ({dur}{error_str}{cache_str})"
            )
            for i, tc in enumerate(tcs):
                is_last = i == len(tcs) - 1
                connector = "└──" if is_last else "├──"
                for line in _tool_line(tc, "│   ", connector):
                    lines.append(line)
            lines.append("│")

        elif name == "synthesis":
            lines.append(f"├── **Phase 4: Synthesis** ({dur})")
            if ar.report_path:
                lines.append(f"│   └── {Path(ar.report_path).name}")
            lines.append("│")

        else:
            rq = context.research_questions[rq_idx] if rq_idx < len(context.research_questions) else None
            rq_idx += 1

            rq_title = rq.title if rq else name
            rq_id = rq.id if rq else name
            cache_hits = sum(1 for tc in tcs if tc.result and "[cached]" in tc.result)
            error_str = f", {errors} errors" if errors else ""
            cache_str = f", {cache_hits} cached" if cache_hits else ""
            findings_count = sum(1 for tc in tcs if tc.tool_name == "record_finding" and not tc.error)
            charts_count = sum(1 for tc in tcs if tc.tool_name == "create_chart" and not tc.error)

            phase_label = "Phase 3" if not recovery_results else "Phase 3"
            lines.append(
                f"├── **{rq_id}:** {rq_title} — "
                f"{len(tcs)} tools ({dur}{error_str}{cache_str})"
            )

            if findings_count or charts_count:
                parts = []
                if findings_count:
                    parts.append(f"{findings_count} findings")
                if charts_count:
                    parts.append(f"{charts_count} charts")
                lines.append(f"│   📊 {', '.join(parts)}")

            for i, tc in enumerate(tcs):
                is_last = i == len(tcs) - 1
                connector = "└──" if is_last else "├──"
                for line in _tool_line(tc, "│   ", connector):
                    lines.append(line)
            lines.append("│")

    if recovery_results:
        lines.append("├── **Phase 3.5: Recovery**")
        for ar in recovery_results:
            tcs = ar.trace.tool_calls
            errors = sum(1 for tc in tcs if tc.error)
            dur = _format_duration(ar.duration_ms)
            error_str = f", {errors} errors" if errors else ""
            lines.append(
                f"│   ├── retry: {ar.agent_name} — "
                f"{len(tcs)} tools ({dur}{error_str})"
            )
            for i, tc in enumerate(tcs):
                is_last = i == len(tcs) - 1
                connector = "└──" if is_last else "├──"
                for line in _tool_line(tc, "│   │   ", connector):
                    lines.append(line)
        lines.append("│")

    all_results = list(agent_results) + list(recovery_results)
    total_tools = sum(len(ar.trace.tool_calls) for ar in all_results)
    total_errors = sum(
        1 for ar in all_results for tc in ar.trace.tool_calls if tc.error
    )
    total_findings = sum(
        1 for ar in all_results
        for tc in ar.trace.tool_calls
        if tc.tool_name == "record_finding" and not tc.error
    )
    total_charts = sum(
        1 for ar in all_results
        for tc in ar.trace.tool_calls
        if tc.tool_name == "create_chart" and not tc.error
    )
    total_open_qs = sum(
        1 for ar in all_results
        for tc in ar.trace.tool_calls
        if tc.tool_name == "add_open_question" and not tc.error
    )

    lines.append("└── **Summary**")
    lines.append(f"    ├── {len(agent_results)} agents, {total_tools} tool calls")
    lines.append(f"    ├── {total_errors} errors ({total_errors / max(total_tools, 1):.0%} error rate)")
    lines.append(f"    ├── {total_findings} findings, {total_charts} charts")
    lines.append(f"    └── {total_open_qs} open questions")
    lines.append("")

    return "\n".join(lines)


def save_tree(
    result: "SpineResult",
    context: InvestigationContext,
    run_dir: str | Path,
) -> Path:
    """Generate and save tree.md in the run directory."""
    tree_md = generate_tree(result, context)
    path = Path(run_dir) / "tree.md"
    path.write_text(tree_md, encoding="utf-8")
    return path

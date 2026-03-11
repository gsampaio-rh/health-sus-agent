"""Tests for InvestigationTracer."""

import json

from src.agent.tracer import InvestigationTracer


def test_tracer_creates_run_directory(tmp_path):
    tracer = InvestigationTracer(logs_dir=tmp_path)
    run_dir = tracer.run_dir

    assert run_dir.exists()
    assert (run_dir / "run.log").exists()


def test_tracer_log_event_appends_to_events(tmp_path):
    tracer = InvestigationTracer(logs_dir=tmp_path)

    tracer.log_event("test_event", {"key": "value"})
    tracer.log_event("second_event")

    assert len(tracer.events) == 2
    assert tracer.events[0]["type"] == "test_event"
    assert tracer.events[0]["key"] == "value"
    assert tracer.events[1]["type"] == "second_event"


def test_tracer_save_plan(tmp_path):
    tracer = InvestigationTracer(logs_dir=tmp_path)

    plan = {"question": "test?", "steps": ["a", "b"]}
    tracer.save_plan(plan)

    plan_file = tracer.run_dir / "plan.json"
    assert plan_file.exists()

    loaded = json.loads(plan_file.read_text())
    assert loaded["question"] == "test?"


def test_tracer_save_step_result(tmp_path):
    tracer = InvestigationTracer(logs_dir=tmp_path)

    tracer.save_step_result(
        step_index=0,
        step_name="overview",
        code='print("hi")',
        output="hi",
        error=None,
        artifacts=[],
        decision="pass",
        summary="Good analysis.",
        duration_ms=1234,
    )

    step_file = tracer.run_dir / "step_00_overview.json"
    assert step_file.exists()

    loaded = json.loads(step_file.read_text())
    assert loaded["decision"] == "pass"
    assert loaded["duration_ms"] == 1234
    assert loaded["code"] == 'print("hi")'


def test_tracer_save_summary_and_trace(tmp_path):
    tracer = InvestigationTracer(logs_dir=tmp_path)

    tracer.log_event("started", {"question": "test"})
    tracer.log_event("completed", {"passed": 2, "total": 3})

    tracer.save_summary({
        "run_id": tracer.run_id,
        "passed": 2,
        "total": 3,
    })

    summary_file = tracer.run_dir / "summary.json"
    trace_file = tracer.run_dir / "trace.json"

    assert summary_file.exists()
    assert trace_file.exists()

    trace = json.loads(trace_file.read_text())
    assert len(trace) == 2
    assert trace[0]["type"] == "started"
    assert trace[1]["type"] == "completed"


def test_tracer_run_id_format(tmp_path):
    tracer = InvestigationTracer(logs_dir=tmp_path)
    assert len(tracer.run_id) == 15  # YYYYMMDD_HHMMSS
    assert "_" in tracer.run_id

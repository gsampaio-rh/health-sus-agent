"""Tests for the Analysis Engine (REPL sandbox + trace)."""

import json
from pathlib import Path

import pytest

from src.agent.engine import AnalysisEngine, ReplSandbox


@pytest.fixture
def tmp_output(tmp_path):
    return tmp_path / "outputs"


class TestReplSandbox:
    def test_basic_execution(self, tmp_output):
        sandbox = ReplSandbox(output_dir=tmp_output)
        output, error, artifacts = sandbox.execute("print(2 + 2)")
        assert output.strip() == "4"
        assert error is None
        assert artifacts == []

    def test_persistent_namespace(self, tmp_output):
        sandbox = ReplSandbox(output_dir=tmp_output)
        sandbox.execute("x = 42")
        output, error, _ = sandbox.execute("print(x)")
        assert output.strip() == "42"
        assert error is None

    def test_preloaded_libraries(self, tmp_output):
        sandbox = ReplSandbox(output_dir=tmp_output)
        output, error, _ = sandbox.execute("print(type(pd).__name__)")
        assert "module" in output
        assert error is None

    def test_error_capture(self, tmp_output):
        sandbox = ReplSandbox(output_dir=tmp_output)
        output, error, _ = sandbox.execute("1 / 0")
        assert error is not None
        assert "ZeroDivisionError" in error

    def test_save_plot_helper(self, tmp_output):
        sandbox = ReplSandbox(output_dir=tmp_output)
        code = """\
fig, ax = plt.subplots()
ax.plot([1, 2, 3], [1, 4, 9])
save_plot(fig, "test_chart")
"""
        output, error, artifacts = sandbox.execute(code)
        assert error is None
        assert len(artifacts) == 1
        assert Path(artifacts[0]).exists()
        assert "test_chart.png" in artifacts[0]

    def test_save_metrics_helper(self, tmp_output):
        sandbox = ReplSandbox(output_dir=tmp_output)
        code = 'save_metrics({"accuracy": 0.95}, "test_metrics")'
        output, error, artifacts = sandbox.execute(code)
        assert error is None
        assert len(artifacts) == 1
        with open(artifacts[0]) as f:
            data = json.load(f)
        assert data["accuracy"] == 0.95

    def test_output_truncation(self, tmp_output):
        sandbox = ReplSandbox(output_dir=tmp_output, max_output_chars=100)
        code = "print('x' * 200)"
        output, error, _ = sandbox.execute(code)
        assert len(output) < 200
        assert "truncated" in output

    def test_timeout(self, tmp_output):
        sandbox = ReplSandbox(output_dir=tmp_output, timeout_seconds=1)
        code = """\
import time
time.sleep(5)
"""
        output, error, _ = sandbox.execute(code)
        assert error is not None
        assert "timeout" in error.lower()


class TestAnalysisEngine:
    def test_execute_appends_trace(self, tmp_output):
        engine = AnalysisEngine(output_dir=tmp_output)
        result = engine.execute("print('hello')", node="test_node")
        assert result.node == "test_node"
        assert result.output.strip() == "hello"
        assert result.error is None
        assert result.duration_ms >= 0
        assert len(engine.trace) == 1
        assert engine.trace[0] is result

    def test_multiple_executions_build_trace(self, tmp_output):
        engine = AnalysisEngine(output_dir=tmp_output)
        engine.execute("x = 1", node="step1")
        engine.execute("x += 1", node="step2")
        result = engine.execute("print(x)", node="step3")
        assert result.output.strip() == "2"
        assert len(engine.trace) == 3

    def test_namespace_property(self, tmp_output):
        engine = AnalysisEngine(output_dir=tmp_output)
        engine.execute("my_var = [1, 2, 3]")
        assert engine.namespace["my_var"] == [1, 2, 3]

    def test_pandas_available(self, tmp_output):
        engine = AnalysisEngine(output_dir=tmp_output)
        result = engine.execute(
            "df = pd.DataFrame({'a': [1, 2, 3]}); print(len(df))",
            node="pandas_test",
        )
        assert result.output.strip() == "3"
        assert result.error is None

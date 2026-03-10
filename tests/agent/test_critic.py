"""Tests for the Critic (5-test quality gate)."""

import json

from src.agent.critic import Critic, _build_user_prompt, _parse_response
from src.agent.state import CodeExecution, CriticDecision

# ---------------------------------------------------------------------------
# Test prompt construction
# ---------------------------------------------------------------------------


def test_build_user_prompt_includes_code():
    execution = CodeExecution(
        node="eda",
        code="df.groupby('year').size()",
        output="2016  5000\n2017  6000",
    )
    prompt = _build_user_prompt(execution, findings_summary="")
    assert "df.groupby('year').size()" in prompt
    assert "2016  5000" in prompt


def test_build_user_prompt_includes_findings():
    execution = CodeExecution(node="eda", code="pass", output="ok")
    prompt = _build_user_prompt(execution, findings_summary="Mortality is 33%")
    assert "Mortality is 33%" in prompt


def test_build_user_prompt_includes_error():
    execution = CodeExecution(
        node="eda", code="1/0", output="", error="ZeroDivisionError"
    )
    prompt = _build_user_prompt(execution, findings_summary="")
    assert "ZeroDivisionError" in prompt


def test_build_user_prompt_includes_artifacts():
    execution = CodeExecution(
        node="eda",
        code="save_plot(fig, 'test')",
        output="",
        artifacts=["outputs/plots/test.png"],
    )
    prompt = _build_user_prompt(execution, findings_summary="")
    assert "outputs/plots/test.png" in prompt


# ---------------------------------------------------------------------------
# Test response parsing
# ---------------------------------------------------------------------------


SAMPLE_PASS_RESPONSE = json.dumps({
    "verdicts": [
        {"test_name": "circularity", "passed": True, "reasoning": "Not tautological"},
        {"test_name": "depth", "passed": True, "reasoning": "Decomposes by year"},
        {"test_name": "surprise", "passed": True, "reasoning": "Post-COVID shift is notable"},
        {"test_name": "confounders", "passed": True, "reasoning": "Age not yet controlled"},
        {"test_name": "so_what", "passed": True, "reasoning": "Implies policy response needed"},
    ],
    "decision": "pass",
    "summary": "Solid initial analysis of mortality trends.",
    "suggestions": [],
})

SAMPLE_DEEPEN_RESPONSE = json.dumps({
    "verdicts": [
        {"test_name": "circularity", "passed": True, "reasoning": "ok"},
        {
            "test_name": "depth",
            "passed": False,
            "reasoning": "Only top-level trend, no decomposition",
        },
        {"test_name": "surprise", "passed": True, "reasoning": "Post-COVID shift"},
        {
            "test_name": "confounders",
            "passed": False,
            "reasoning": "Age and comorbidities not controlled",
        },
        {"test_name": "so_what", "passed": True, "reasoning": "Policy relevant"},
    ],
    "decision": "deepen",
    "summary": "Direction is sound but needs decomposition and confounder control.",
    "suggestions": ["Break down mortality by age group", "Control for comorbidity count"],
})


def test_parse_pass_response():
    reflection = _parse_response(SAMPLE_PASS_RESPONSE)
    assert reflection.decision == CriticDecision.PASS
    assert reflection.passed is True
    assert len(reflection.verdicts) == 5
    assert all(v.passed for v in reflection.verdicts)


def test_parse_deepen_response():
    reflection = _parse_response(SAMPLE_DEEPEN_RESPONSE)
    assert reflection.decision == CriticDecision.DEEPEN
    assert reflection.passed is False
    assert len(reflection.failed_tests) == 2
    assert reflection.failed_tests[0].test_name == "depth"


def test_parse_response_with_markdown_wrapping():
    wrapped = f"```json\n{SAMPLE_PASS_RESPONSE}\n```"
    reflection = _parse_response(wrapped)
    assert reflection.decision == CriticDecision.PASS


# ---------------------------------------------------------------------------
# Test Critic with mock LLM
# ---------------------------------------------------------------------------


class MockLLM:
    """Fake LLM that returns a canned response."""

    def __init__(self, response_text: str):
        self._response_text = response_text

    def invoke(self, messages):
        class FakeResponse:
            content = self._response_text
        return FakeResponse()


def test_critic_evaluate_returns_reflection():
    critic = Critic(llm=MockLLM(SAMPLE_PASS_RESPONSE))
    execution = CodeExecution(
        node="eda",
        code="print(df['MORTE'].mean())",
        output="0.33",
    )
    reflection = critic.evaluate(execution, findings_summary="")
    assert reflection.decision == CriticDecision.PASS
    assert len(reflection.verdicts) == 5


def test_critic_evaluate_deepen():
    critic = Critic(llm=MockLLM(SAMPLE_DEEPEN_RESPONSE))
    execution = CodeExecution(
        node="eda",
        code="df.groupby('year').size()",
        output="yearly counts",
    )
    reflection = critic.evaluate(execution)
    assert reflection.decision == CriticDecision.DEEPEN
    assert len(reflection.suggestions) == 2

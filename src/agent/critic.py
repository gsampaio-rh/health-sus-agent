"""Critic — LLM-based quality gate with 5 tests.

Evaluates each analysis step against circularity, depth, surprise,
confounders, and "so what?" tests. Returns a Reflection with per-test
verdicts and an overall pass/fail decision.
"""

from __future__ import annotations

import json

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.agent.state import CodeExecution, CriticDecision, CriticVerdict, Reflection

DOMAIN_PRIORS = [
    "Older patients have higher mortality",
    "ICU hospitals are concentrated in large cities",
    "Emergency admissions have worse outcomes than elective",
    "COVID caused a spike in respiratory mortality in 2020-2021",
    "Public hospitals treat more complex cases than private",
    "Longer length of stay correlates with worse outcomes",
]

SYSTEM_PROMPT = """\
You are a research quality critic for public health investigations using \
Brazilian SUS (Sistema Unico de Saude) data. Your job is to evaluate whether \
an analysis step produces genuine insight or falls into common AI research \
failure modes.

IMPORTANT CALIBRATION:
- Most well-constructed analyses should PASS most tests.
- Only flag a test as FAILED if there is a clear, specific violation.
- "Could be improved" is NOT the same as "fails" — only flag genuine flaws.
- An analysis that controls for confounders, decomposes findings, and \
connects to policy PASSES even if further analysis is possible.
- Reserve "fail" for analyses with fundamental methodological problems.

You will receive:
1. The Python code that was executed
2. The output it produced (stdout, metrics, chart descriptions)
3. Previously established findings (if any)
4. A list of domain priors — things the audience already knows

Evaluate the analysis against these 5 tests:

## Test 1: Circularity
FAILS if the finding restates the input in a different shape. Examples: \
"patients who died had higher mortality" (tautology), "cities with more \
cases have more deaths" (correlating a count with its subset).
PASSES if the analysis reveals a non-obvious relationship, compares \
competing explanations, or produces a result that is not definitionally \
true. Example: "age explains 97% of mortality variance while ICU capacity \
explains only 6%" — this compares two plausible explanations and produces \
a non-obvious winner.

## Test 2: Depth
FAILS if the analysis reports only a single aggregate number or a simple \
trend with no decomposition. Example: "mortality is 33%" or a line chart \
with no breakdown.
PASSES if the analysis breaks a finding into components along at least \
one dimension (age, geography, time, facility type, procedure). Example: \
"volume growth is 64% ureteroscopy, 36% legacy procedures" decomposes the \
top-level number into specific, actionable components.

## Test 3: Surprise
FAILS if the finding only restates a domain prior from the provided list. \
Example: "older patients have higher mortality" when that is listed as a \
known prior.
PASSES if the finding contradicts a prior, quantifies something previously \
vague, reveals an unexpected pattern, or shows that an effect survives \
confounder adjustment (the audience did not know it would survive). A \
finding does NOT need to be shocking — merely non-obvious is sufficient.

## Test 4: Confounders
FAILS if the analysis compares groups (hospitals, cities, demographics) \
without controlling for any plausible confounder, AND the comparison is \
the main finding. Example: ranking hospitals by raw mortality without \
case-mix adjustment.
PASSES if the analysis controls for at least one relevant confounder \
(age, severity, case-mix), OR if the finding is descriptive rather than \
comparative, OR if confounders are acknowledged. Not every analysis must \
control for every possible variable.

## Test 5: So What?
FAILS if the output is purely descriptive with no connection to action. \
Example: reporting R-squared with no interpretation, or listing \
correlations without implications.
PASSES if the analysis names a specific intervention target, policy \
change, resource allocation decision, or investigation direction. \
Example: "invest in geriatric respiratory care, not ICU expansion" or \
"these 22 hospitals are intervention targets."

Respond with ONLY valid JSON matching this schema:
{
  "verdicts": [
    {
      "test_name": "circularity" | "depth" | "surprise" | "confounders" | "so_what",
      "passed": true | false,
      "reasoning": "One sentence explanation"
    }
  ],
  "decision": "pass" | "fail" | "deepen",
  "summary": "One paragraph overall assessment",
  "suggestions": ["Specific suggestion for improvement if any test failed"]
}

Decision rules:
- "pass": 0-1 tests fail. The analysis has genuine insight.
- "fail": circularity fails, OR 4+ tests fail. Fundamentally flawed.
- "deepen": 2-3 tests fail and the direction is sound but needs work.
When in doubt between pass and deepen, choose pass.
When in doubt between deepen and fail, choose deepen.
"""


def _build_user_prompt(
    execution: CodeExecution,
    findings_summary: str,
    domain_priors: list[str] | None = None,
) -> str:
    priors = domain_priors or DOMAIN_PRIORS
    priors_text = "\n".join(f"- {p}" for p in priors)

    artifacts_text = ""
    if execution.artifacts:
        artifacts_text = "\n".join(f"- {a}" for a in execution.artifacts)
        artifacts_text = f"\n\n## Artifacts produced\n{artifacts_text}"

    error_text = ""
    if execution.error:
        error_text = f"\n\n## Execution error\n```\n{execution.error}\n```"

    return f"""\
## Code executed (node: {execution.node})
```python
{execution.code}
```

## Output
```
{execution.output}
```
{error_text}{artifacts_text}

## Previously established findings
{findings_summary or "None yet — this is the first analysis step."}

## Domain priors (things the audience already knows)
{priors_text}
"""


def _extract_json(raw: str) -> str:
    """Extract JSON from LLM output, handling thinking tags and markdown."""
    import re

    text = raw.strip()

    # Strip <think>...</think> blocks (qwen3, deepseek, etc.)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    # Strip markdown code fences
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    # If still not valid JSON, try to find first { ... last }
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]

    return text


def _parse_response(raw: str) -> Reflection:
    """Parse LLM JSON response into a Reflection."""
    text = _extract_json(raw)
    data = json.loads(text)

    verdicts = [
        CriticVerdict(
            test_name=v["test_name"],
            passed=v["passed"],
            reasoning=v["reasoning"],
        )
        for v in data["verdicts"]
    ]

    decision_map = {
        "pass": CriticDecision.PASS,
        "fail": CriticDecision.FAIL,
        "deepen": CriticDecision.DEEPEN,
    }

    return Reflection(
        phase="critic",
        verdicts=verdicts,
        decision=decision_map[data["decision"]],
        summary=data["summary"],
        suggestions=data.get("suggestions", []),
    )


class Critic:
    """LLM-based quality gate that evaluates analysis steps."""

    def __init__(
        self,
        llm: BaseChatModel,
        domain_priors: list[str] | None = None,
    ):
        self.llm = llm
        self.domain_priors = domain_priors or DOMAIN_PRIORS

    def evaluate(
        self,
        execution: CodeExecution,
        findings_summary: str = "",
    ) -> Reflection:
        """Run the 5-test quality evaluation on a code execution result."""
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=_build_user_prompt(
                    execution, findings_summary, self.domain_priors
                )
            ),
        ]

        response = self.llm.invoke(messages)
        return _parse_response(response.content)

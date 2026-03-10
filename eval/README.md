# Critic Evaluation Dataset

Measures whether the Critic correctly identifies good vs bad analyses across the 5 quality tests.

## Quick start

```bash
# With Ollama (local)
AGENT_LLM_PROVIDER=openai \
AGENT_LLM_BASE_URL=http://localhost:11434/v1 \
AGENT_LLM_MODEL=gemma3:12b-it-q8_0 \
AGENT_LLM_API_KEY=not-needed \
python -m eval.run_critic_eval

# With Anthropic
AGENT_LLM_PROVIDER=anthropic \
python -m eval.run_critic_eval

# With OpenAI
AGENT_LLM_PROVIDER=openai \
python -m eval.run_critic_eval
```

## Dataset

20 evaluation cases across 6 categories:

| Category | Cases | What it tests |
|---|---|---|
| **pass** | 4 | Good analyses that should pass all 5 tests |
| **fail_circularity** | 3 | Tautologies, restatements, severity proxies |
| **fail_depth** | 3 | Bare statistics, no decomposition |
| **fail_surprise** | 3 | Findings that restate domain priors |
| **fail_confounders** | 3 | Missing case-mix, age standardization |
| **fail_so_what** | 4 | No policy connection or action path |

Cases are derived from verified findings in the kidney (N20) and respiratory failure (J96) experiments.

## Metrics

- **Decision accuracy** — Did the Critic return the correct pass/fail/deepen decision?
- **Per-test accuracy** — For each of the 5 tests, did the Critic correctly identify pass vs fail?
- **Overall test accuracy** — Across all cases and tests, what fraction were correct?

## Interpreting results

**Decision accuracy > 80%** — The Critic is usable as a quality gate. It will catch most bad analyses and let most good ones through.

**Per-test accuracy < 70% on a specific test** — That test's prompt needs refinement. Check the misclassified cases to understand the failure mode.

**Common failure patterns:**

- Critic passes `fail_surprise` cases — the surprise test prompt may need stronger domain priors
- Critic fails `pass` cases on confounders — the Critic may be too strict about explicit confounder control
- Critic passes `fail_circularity` cases — the circularity detection prompt needs more examples

## Output

Results are saved to `eval/results/` as JSON with timestamps and model names. Compare across models:

```bash
# Run on multiple models
for model in gemma3:12b-it-q8_0 qwen2.5:7b llama3.1:8b; do
  AGENT_LLM_PROVIDER=openai \
  AGENT_LLM_BASE_URL=http://localhost:11434/v1 \
  AGENT_LLM_MODEL=$model \
  AGENT_LLM_API_KEY=not-needed \
  python -m eval.run_critic_eval
done
```

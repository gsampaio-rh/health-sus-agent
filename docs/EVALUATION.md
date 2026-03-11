# Evaluation and Interpretation

How to assess whether the agent produced good results, interpret run outputs, and diagnose problems.

## Reading Run Outputs

Each run produces a directory under `runs/{run_id}/`:

| File/Directory | What it contains |
|----------------|-----------------|
| `context.json` | Final investigation state: question, RQs, datasets loaded, data catalog, findings, open questions |
| `FINDINGS.md` | Top-level findings in human-readable format |
| `reports/00_plan.md` | Investigation plan from DirectorAgent |
| `reports/01_data_report.md` | Data quality profile from DataAgent |
| `reports/NN_rq_*.md` | Per-question research reports from RQ agents |
| `reports/executive_summary.md` | Consolidated summary from SynthesisAgent |
| `plots/*.png` | All charts generated during the investigation |
| `traces/*_trace.json` | Per-agent execution traces (tool calls, timing, errors) |

### Where to start

1. Read `reports/executive_summary.md` for the high-level narrative
2. Check `FINDINGS.md` for all findings with confidence levels
3. Browse `plots/` for the visualizations
4. If something looks wrong, check the corresponding `traces/` file

## Interpreting Trace Files

Each agent produces a trace JSON with this structure:

```json
{
  "agent": "rq_mortality_trend",
  "scratchpad": "## Goal\n...\n## Observations\n...",
  "tool_calls": [
    {
      "tool": "aggregate",
      "args": {"dataset": "resp_failure_sih", "group_by": ["year"], ...},
      "result": "  year  admissions  mortality_rate\n0 2016  ...",
      "error": null,
      "duration_ms": 45
    }
  ],
  "artifacts": ["runs/.../plots/01_mortality_trend.png"],
  "llm_reasoning": "",
  "duration_ms": 54934
}
```

### Key fields

| Field | What to check |
|-------|---------------|
| `tool_calls[].error` | If non-null, the tool call failed. The error message explains why. |
| `tool_calls[].result` | The tool's output. Should NOT start with "Error". If it does, error routing may have failed. |
| `tool_calls[].duration_ms` | `0` means a cache hit. Very high values may indicate an LLM hang. |
| `scratchpad` | The agent's reasoning: goal, observations, hypotheses, conclusions. |
| `llm_reasoning` | Raw LLM output when no tool calls were parsed (final round). |

### Spotting problems in traces

**Empty datasets**: Look for `"result": "Filtered ... 0 rows"` or `"result": "Empty DataFrame"`. This means a filter matched nothing, often due to exact ICD matching instead of prefix matching.

**Cache hits**: Results prefixed with `[cached]` came from the ArtifactStore, not fresh computation. This is normal and expected on subsequent runs.

**Repeated tool calls**: If the same tool is called multiple times with the same args, the agent is likely confused. Check if earlier results contained errors that the LLM misunderstood.

## Quality Metrics

After a run, compute these metrics from the trace files:

### Error rate

```bash
# Quick error count from logs
grep "Spine Complete" runs/{run_id}/../../*.log
# Shows: "X tool calls (Y errors)"
```

| Error rate | Assessment |
|------------|------------|
| < 5% | Excellent — agent is operating cleanly |
| 5-15% | Acceptable — some self-correction happening |
| 15-30% | Concerning — check which tools are failing |
| > 30% | Poor — may need prompt or tool improvements |

### Tool call count

| Agent | Typical range | Too few | Too many |
|-------|---------------|---------|----------|
| DataAgent | 15-25 | May have skipped profiling | May be looping on errors |
| RQAgent | 5-30 | Shallow analysis | Thrashing / retrying |
| Total | 100-250 | Investigation may be shallow | May be hitting max rounds |

### Cache effectiveness

On second runs with unchanged source data:
- DataAgent should log `"Cache valid — restored N cached datasets"`
- Tool calls with `duration_ms: 0` are cache hits
- Cache hit ratio = (cache hits / total cacheable tool calls)

### Recovery triggers

If the recovery phase runs, check:
- Which agents were retried (error rate > 30%, >= 3 errors)
- Whether the retry reduced errors
- What `prior_errors` were injected

## Critic Evaluation

The Critic is a 5-test quality gate that evaluates analysis quality. It can be run independently against a dataset of 20 test cases.

### The five tests

| Test | Question | Catches |
|------|----------|---------|
| Circularity | Is the conclusion embedded in the premise? | "Patients who died had higher mortality" |
| Depth | Does this decompose beyond top-level numbers? | Bare statistics without breakdown |
| Surprise | Would a domain expert say "I didn't know that"? | Restating what everyone already knows |
| Confounders | Is there an omitted variable that could explain this? | Missing age/case-mix adjustment |
| So-what | What should someone DO differently? | No policy connection |

### Running the Critic evaluation

```bash
AGENT_LLM_PROVIDER=openai \
AGENT_LLM_BASE_URL=http://localhost:11434/v1 \
AGENT_LLM_MODEL=gpt-oss:120b-cloud \
AGENT_LLM_API_KEY=ollama \
python -m eval.run_critic_eval
```

### Evaluation dataset

20 cases across 6 categories:

| Category | Cases | What it tests |
|----------|-------|---------------|
| pass | 4 | Good analyses that should pass all 5 tests |
| fail_circularity | 3 | Tautologies, restatements |
| fail_depth | 3 | Bare statistics, no decomposition |
| fail_surprise | 3 | Findings that restate domain priors |
| fail_confounders | 3 | Missing case-mix, age standardization |
| fail_so_what | 4 | No policy connection |

### Interpreting results

- **Decision accuracy > 80%**: The Critic is usable as a quality gate
- **Per-test accuracy < 70%**: That test's prompt needs refinement
- **Common false negatives**: Critic passes `fail_surprise` cases — the surprise test may need stronger domain priors
- **Common false positives**: Critic fails `pass` cases on confounders — the Critic may be too strict

Results are saved to `eval/results/` as JSON with timestamps and model names.

### Model comparison

```bash
for model in gpt-oss:120b-cloud gemma3:12b-it-q8_0 qwen3:8b; do
  AGENT_LLM_PROVIDER=openai \
  AGENT_LLM_BASE_URL=http://localhost:11434/v1 \
  AGENT_LLM_MODEL=$model \
  AGENT_LLM_API_KEY=ollama \
  python -m eval.run_critic_eval
done
```

## Common Failure Patterns

### Exact ICD matching returns 0 rows

**Symptom**: `filter_dataset` returns `"0 rows"` when filtering for an ICD code like `J96`.

**Cause**: The data contains subcodes (`J960`, `J961`, `J969`) — exact matching finds nothing.

**Fix**: The agent should use prefix matching: `{"DIAG_PRINC": "J96*"}` or `{"DIAG_PRINC": {"startswith": "J96"}}`. The tool now returns a helpful error with sample values when 0 rows result.

### Template placeholders in findings

**Symptom**: A finding says `"Total admissions: {admissions}, mortality: {rate:.2%}"`.

**Cause**: The LLM used Python f-string placeholders instead of actual values from tool results.

**Fix**: `record_finding` detects `{variable}` patterns and returns an error asking for actual numbers.

### Charts from empty datasets

**Symptom**: Blank PNG charts in `plots/` or `cache/plots/`.

**Cause**: A chart was generated from a 0-row dataset (e.g., after a failed filter).

**Fix**: `create_chart` now returns an error for empty datasets. The cache refuses to store 0-row datasets and charts from empty data.

### Error strings in result field

**Symptom**: In a trace file, `"result"` contains an error message but `"error"` is `null`.

**Cause**: The tool returned an error string that wasn't caught by the error routing logic.

**Fix**: `execute_tool` now catches both `"Error:"` and `"Error "` prefixes. If you still see this pattern, the tool needs to be updated to use the `"Error:"` prefix.

## Comparing Runs

When running the same question multiple times (e.g., with different models or cache states):

| What to compare | Where to find it |
|-----------------|-----------------|
| Total duration | Spine log: `"Spine Complete: Xms total"` |
| Error rate | Spine log: `"Y tool calls (Z errors)"` |
| Number of RQs | `context.json` → `research_questions` length |
| Cache effectiveness | Spine log: `"cache: N datasets, M charts"` |
| Finding count | `FINDINGS.md` or `context.json` → `findings` length |
| Report quality | Manual review of `executive_summary.md` |

Note: The DirectorAgent is non-deterministic — it may produce different research questions each run. This means tool call counts and specific findings will vary even with the same question and data. Compare at the quality level (are findings deep? non-circular? actionable?) rather than exact reproduction.

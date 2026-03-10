# START HERE — Building the Research Agent

> You're building an autonomous agent that takes a health research question and produces a complete investigation. Read this doc first, then the references, then start coding.

---

## What Exists Today

### The problem we solved manually (twice)

Two complete investigations were done by a human directing an AI in a chat conversation:

| Experiment | Condition | Notebooks | Key Outcome |
|---|---|---|---|
| `experiments/kidney/` | Kidney stones (N20) | 13 | Volume crisis: 41% growth, hospital efficiency variation, reallocation model |
| `experiments/respiratory_failure/` | Respiratory failure (J96) | 9 | Mortality crisis: +4.4pp post-COVID, age explains 97%, 982 saveable lives/yr |

Each took ~25 human–AI interactions over multiple sessions. The human acted as research director — setting quality bars, requesting decompositions, identifying missing data sources, connecting findings to policy.

### The codebase

| Path | What It Does |
|---|---|
| `src/` | Data pipeline — downloads SIH, CNES, SIM, SINAN, SIA from DATASUS via PySUS. Hexagonal architecture (ports/adapters). CLI: `sus-pipeline download SIH --years 2016-2025 --uf SP` |
| `data/` | Raw parquet files (gitignored). SIH, CNES, SIM, plus IBGE census/estimates |
| `experiments/*/notebooks/shared.py` | Per-experiment helpers: data loaders, plot utilities, constants |
| `experiments/*/EXPERIMENT.md` | Pre-registered research questions and hypotheses |
| `experiments/*/PLAN.md` | Notebook execution plan with sprint breakdown |

### The documents you must read

1. **`docs/AGENT_LESSONS_LEARNED.md`** — The most important doc. Captures five failure modes of AI research (circular findings, satisficing, no counterfactual imagination, statistics without meaning, linear execution) and the architecture to fix them. **Read this first.**

2. **`docs/PRD_LANGGRAPH_AGENT.md`** — Earlier PRD with LangGraph architecture, state schema, REPL design, and MCP integration plan. Some parts are superseded by the lessons learned doc (especially: notebooks are output, not execution). Use as reference for state schema and tool design.

3. **`experiments/respiratory_failure/EXPERIMENT.md`** — Example of a complete experiment specification. Shows the level of rigor expected: research questions, hypotheses, data sources, inclusion criteria, causal rigor notes.

4. **`experiments/respiratory_failure/notebooks/shared.py`** — Example of the helper layer that each experiment uses. Data loading, plot styling, metrics saving.

---

## What You're Building

An agent that automates what the human did in those 25 interactions — except better, because it won't need the human to say "this is lazy" or "get IBGE data."

### Input

```
"Investigate respiratory failure mortality in São Paulo SUS"
```

or more precisely:

```python
{
    "question": "Why is respiratory failure mortality rising in São Paulo?",
    "icd10_prefix": "J96",
    "uf": "SP",
    "year_range": (2016, 2025),
    "audience": "Brazilian health policymakers",
    "language": "pt-BR",
}
```

### Output

- Execution trace (structured log of all code, outputs, decisions)
- Findings accumulator (JSON of established facts, open questions, contradictions)
- Charts (PNGs)
- Metrics (JSON per analysis step)
- Reports (markdown, inline charts, audience language)
- Reproducibility notebooks (generated FROM the trace, not the execution format)

### The Five Components

| Component | Role | Why It Matters |
|---|---|---|
| **Planner** | Sets audience, language, data sources, enrichments, quality criteria upfront | Prevents mid-investigation "oh we need IBGE data" |
| **Analysis Engine** | Python REPL that executes code and logs everything to a structured trace | The workhorse — writes and runs pandas/scipy/matplotlib |
| **Critic** | Runs after each analysis step. Five tests: circularity, depth, surprise, confounders, "so what?" | Replaces the human saying "this is lazy." The highest-impact component. |
| **Findings Accumulator** | Persistent cross-step knowledge. Facts, contradictions, open questions. | Prevents linear thinking. Propagates new insights back. |
| **Output Renderer** | Generates notebooks, reports, metrics FROM the execution trace | Notebooks are output, not execution. |

See `docs/AGENT_LESSONS_LEARNED.md` § 4.2–4.6 for full architecture description.

---

## Key Design Decisions (Already Made)

These were learned the hard way. Don't revisit them.

1. **Notebooks are output, not execution.** The agent runs code, logs to a trace, and renders notebooks at the end for humans. Don't build notebook execution into the core loop — it's fragile, sequential, and conflates execution with presentation.

2. **The Critic is the most important component.** Without it, the agent produces technically correct but shallow, circular, or obvious analyses. The five tests (circularity, depth, surprise, confounders, "so what?") are the quality bar.

3. **Data enrichment must be planned upfront.** The Planner consults a registry of external sources (IBGE, IPCA, CNES subgroups) and schedules downloads before analysis begins. Don't let the agent discover it needs data mid-investigation.

4. **Code, not tools.** The agent writes arbitrary Python (pandas, scipy, matplotlib) via a REPL, not fixed pre-built tools. Pre-built tools can't handle "why does Guarulhos have 3x the ER rate?" — only ad-hoc code can.

5. **Depth-1 recursion only.** When the agent finds something unexpected, it can spawn ONE child investigation. No grandchildren. Research (arXiv 2603.02615) shows depth > 1 degrades quality.

6. **3 human checkpoints.** After plan+EDA ("is this the right question?"), after core analysis ("are findings real?"), before final report ("is this actionable?"). Everything else is autonomous.

---

## Sprint 0 — What to Build First

**Goal:** A minimal loop that can run ONE analysis step with the Critic, end to end.

Don't build the full agent. Build the smallest thing that demonstrates the core loop:

```
Planner (hardcoded) → Analysis Engine (1 step) → Critic → pass/fail
```

### Concrete deliverables

1. **State schema** — Define `InvestigationState` (start from PRD § State Schema, update per lessons learned)
2. **Python REPL sandbox** — Persistent namespace, save_plot/save_metrics helpers, execution timeout, output capture
3. **Execution trace** — Structured log: `{step, code, stdout, charts, metrics, duration_ms}`
4. **Critic** — Takes a trace entry + findings so far, runs the 5 tests, returns pass/fail with reasons
5. **One integration test** — Give it "compute J96 mortality by year" as a hardcoded step, verify it produces a chart and the Critic passes it

### What NOT to build yet

- LangGraph graph structure (just use function calls)
- Fan-out/fan-in parallelism
- Subagent recursion
- Report generation
- Notebook rendering
- Human checkpoint UI
- MCP servers

---

## Reference Data for Testing

The respiratory failure experiment data is already processed:

```
experiments/respiratory_failure/outputs/data/resp_failure_sih.parquet
experiments/respiratory_failure/outputs/data/hospital_tags.parquet
experiments/respiratory_failure/outputs/data/hospital_icu_beds.parquet
```

Use these for integration tests. The agent should be able to reproduce the key findings from the J96 investigation:

| Finding | Source | Verification |
|---|---|---|
| Mortality 33%, rising post-COVID | NB02 metrics | `02_general_overview.json` |
| Age explains 97% of mortality variance | NB04 metrics | `04_icu_capacity.json` |
| 22 consistently underperforming hospitals | NB06 metrics | `06_hospital_performance.json` |
| 982 saveable lives/year | NB08 metrics | `08_modifiable_factors.json` |

---

## File Structure

```
src/
├── agent/
│   ├── __init__.py
│   ├── state.py            # InvestigationState, CodeExecution, Finding, etc.
│   ├── planner.py          # Planner component
│   ├── engine.py           # Analysis Engine (REPL wrapper + trace logger)
│   ├── critic.py           # Critic (5 tests)
│   ├── accumulator.py      # Findings Accumulator
│   └── renderer.py         # Output Renderer (notebooks, reports, metrics)
├── domain/                 # Existing — data models and ports
└── infrastructure/         # Existing — DATASUS adapters
```

---

## The Unsolved Problem

The Critic needs to answer: **"Is this finding surprising?"**

That requires a model of what the audience already knows. We don't have a good solution for this yet. For Sprint 0, hardcode domain priors as a list of "things everyone already knows" (e.g., "older patients die more," "ICU hospitals are in cities") and flag findings that only restate those priors.

This is the core research question for the agent itself. Everything else is engineering.

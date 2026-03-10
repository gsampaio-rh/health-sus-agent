# Agent Roadmap

> Sprint-by-sprint plan for building the autonomous research agent.
> Each sprint builds on the previous one. Read `ARCHITECTURE.md` for the
> full technical design. Read `LESSONS_LEARNED.md` for the failure modes
> that drive the architecture.

---

## Sprint 0 — Minimal Loop (DONE)

**Goal:** Prove the core loop works end-to-end with a hardcoded analysis.

**Delivered:**
- `state.py` — `InvestigationState`, `CodeExecution`, `Finding`, `Contradiction`, `Reflection`, `CriticVerdict`
- `engine.py` — `ReplSandbox` (sandboxed Python exec, persistent namespace, `save_plot`/`save_metrics` helpers, timeout, output truncation) + `AnalysisEngine` (trace logger)
- `critic.py` — LLM-based 5-test quality gate (circularity, depth, surprise, confounders, so-what) with calibrated prompt
- `accumulator.py` — `FindingsAccumulator` (facts, contradictions, open questions)
- `runner.py` — Hardcoded J96 mortality analysis → Engine → Critic → Accumulator
- `config.py` — `AgentConfig` via pydantic-settings, supports Anthropic / OpenAI / Ollama
- `eval/` — 20-case Critic dataset, eval runner, `run_sweep.sh`, `compare_results.py`
- 34 unit + integration tests

**Eval results (improved prompt):**

| Model | Decision Acc | Test Acc | Misclassified | Speed |
|---|---|---|---|---|
| qwen3:8b | **70%** | 70% | 6/20 | 666s |
| qwen2.5:7b | 45% | 72% | 11/20 | 263s |
| llama3.1:8b | 40% | 68% | 12/20 | 320s |
| gemma3:12b | 30% | 74% | 14/20 | 634s |
| mistral:7b | 20% | 71% | 16/20 | 184s |

**Key insight:** qwen3:8b is the best local Critic backbone. All models struggle
with the fail→deepen→fail boundary (returning "deepen" when "fail" is expected).
A cloud model (Claude, GPT-4o) would likely perform better but adds latency and cost.

---

## Sprint 1 — Skill-Aware Planner + RLM Code Loop

**Goal:** The agent receives a research question, loads domain knowledge
from the Skill, and autonomously generates + executes + critiques analysis
code in an iterative REPL loop (RLM pattern).

### 1.1 Skill Loader (`src/agent/skill.py`)

Loads `.cursor/skills/sus-deep-dive/SKILL.md` at startup and makes it
available as context for Planner, Code Generator, and Critic:

```python
@dataclass
class SkillContext:
    raw_content: str        # Full SKILL.md text
    data_schemas: str       # Extracted: column names, types, gotchas
    workflow: str           # Extracted: 7-step investigation process
    feature_recipes: str    # Extracted: feature engineering, leakage prevention
    output_standards: str   # Extracted: plot naming, metrics schema, FINDINGS template
    pitfalls: str           # Extracted: common mistakes to avoid
```

The skill is the agent's SUS expertise — without it, the agent writes
`df["SEXO"] == 1` (silently wrong) instead of `df["SEXO"].astype(str) == "1"`.

### 1.2 Planner (`src/agent/planner.py`)

Takes a research question + skill context and produces an investigation plan.
The Planner's system prompt includes the skill content.

```python
@dataclass
class InvestigationPlan:
    question: str
    icd10_prefix: str
    uf: str
    year_range: tuple[int, int]
    audience: str
    language: str
    data_sources: list[str]
    analysis_steps: list[AnalysisStep]
    domain_priors: list[str]
```

The Planner should:
- Parse the research question to identify ICD-10, UF, year range
- Consult skill for available data sources and loading patterns
- Generate 5-8 analysis steps following the skill's investigation workflow
- Extract domain priors from skill + general health knowledge for the Critic

### 1.3 Code Generator (`src/agent/codegen.py`)

Implements the **RLM REPL loop**: the LLM writes code, observes output,
and writes more code iteratively. This is NOT one-shot code generation.

```
Iteration 1:
  LLM receives: step description + skill context + namespace state
  LLM writes:   df.groupby("year")["MORTE"].mean()
  Engine runs:  → output: year, mortality_rate table
  LLM observes: "mortality is 33% overall, rising post-2020"

Iteration 2:
  LLM receives: previous output + "decompose by age group"
  LLM writes:   df.groupby(["year", "age_group"])["MORTE"].mean().unstack()
  Engine runs:  → output: heatmap data
  LLM observes: "age 70+ driving the rise"

Critic evaluates the full step → pass/deepen/fail
```

The Code Generator's system prompt includes the skill content, which
prevents common mistakes (string columns, date parsing, leakage).

### 1.4 Orchestrator (`src/agent/orchestrator.py`)

Replaces the hardcoded `runner.py`. Runs the full loop:

```
plan = planner.create_plan(question, skill)

for step in plan.analysis_steps:
    # RLM loop: iterative code generation + execution
    for iteration in range(max_iterations_per_step):
        code = codegen.generate(step, engine.namespace, accumulator.summary(), skill)
        result = engine.execute(code)

        if codegen.needs_more_iterations(result):
            continue  # LLM observes output, writes more code

    # Critic evaluates the completed step
    reflection = critic.evaluate(result, accumulator.summary())

    if reflection.decision == PASS:
        accumulator.add_finding(...)
    elif reflection.decision == DEEPEN:
        # retry with critic feedback (max 2 retries)
        code = codegen.generate(step + critic.suggestions, ...)
    elif reflection.decision == FAIL:
        log and skip
```

### 1.5 Structured Data Tools

Alongside the REPL, implement structured tools for data loading:

```python
load_sih_data(icd10_prefix, columns, year_range, uf)
load_cnes_data(snapshot, uf)
lookup_icd10(code)
lookup_procedure(code)
lookup_municipality(code)
```

These are deterministic (no LLM needed) and inject data into the REPL
namespace.

### 1.6 Tests

- Unit: Skill loader extracts structured sections from SKILL.md
- Unit: Planner generates valid plan from research question + skill
- Unit: Code Generator produces executable Python with correct SUS patterns
- Integration: Full RLM loop with mock LLM
- Integration: Full loop with real LLM on J96 data

### 1.7 Definition of Done

- [ ] Skill loaded and injected into Planner + Code Generator + Critic
- [ ] Agent accepts "Investigate J96 respiratory failure mortality in SP" and produces findings
- [ ] Code Generator uses RLM loop (iterative, not one-shot)
- [ ] At least 3 analysis steps execute and pass the Critic
- [ ] No hardcoded analysis code in the orchestrator

---

## Sprint 2 — Findings-Driven Iteration + Phase Reflection

**Goal:** The agent uses accumulated findings to decide what to investigate
next, and reflection nodes at phase boundaries ensure depth.

### 2.1 Adaptive Planning

After each analysis step, the Planner can:
- Add new steps based on what was discovered
- Re-prioritize remaining steps based on findings
- Spawn follow-up analyses when contradictions are detected

### 2.2 Phase Reflection (`src/agent/reflection.py`)

Broader than the per-step Critic. Runs at phase boundaries (after EDA,
after hypothesis testing, etc.):

```
Given the work done so far:
1. List dimensions NOT yet explored
2. List potential confounders NOT yet controlled
3. Rate evidence sufficiency: INSUFFICIENT / ADEQUATE / STRONG
4. Decision: DEEPEN / SUBINVESTIGATE / CONTINUE
```

Reflection limits:
- Max 3 loops per phase
- Each loop must address a specific gap
- Force-proceed after 3 with "incomplete" flag

### 2.3 Contradiction Resolution

When the Accumulator detects a contradiction (e.g., "mortality is falling"
vs. new finding "mortality is rising for age 70+"), the orchestrator
automatically generates a resolution step.

### 2.4 Stopping Criteria

The agent knows when to stop:
- All planned steps completed
- No high-priority open questions remain
- Critic passes are consistent (last N steps all pass)
- Maximum iteration limit reached

### 2.5 Definition of Done

- [ ] Phase reflection runs after EDA and prevents shallow analysis
- [ ] Agent adds at least 1 follow-up step not in the original plan
- [ ] Agent resolves at least 1 contradiction autonomously
- [ ] Agent stops before hitting the max iteration limit

---

## Sprint 3 — Data Enrichment Engine

**Goal:** The Planner consults a data source registry and schedules
enrichment downloads before analysis begins.

### 3.1 Data Source Registry (`src/agent/registry.py`)

A structured catalog with enrichment rules:

| Source | Trigger | Data Path |
|---|---|---|
| IBGE Census/Estimates | Geographic comparison | `data/ibge/` |
| IPCA (inflation) | Cost trend analysis | `data/ipca/` |
| CNES subgroups | Hospital comparison | `data/cnes/` |
| SIM (mortality) | Mortality cross-reference | `data/sim/` |
| SINAN (diseases) | Outbreak correlation | `data/sinan/` |
| SINASC (births) | Maternal/neonatal health | `data/sinasc/` |

### 3.2 Enrichment Rules

```
IF geographic_comparison → REQUIRE IBGE population for per-capita rates
IF cost_trend → REQUIRE IPCA for real-value deflation
IF hospital_comparison → REQUIRE CNES case-mix + facility data
IF temporal_trend → REQUIRE population growth for rate adjustment
```

### 3.3 Planner Integration

The Planner checks the registry at plan time and inserts data loading
steps before analyses that need enrichment. This prevents the
mid-investigation "oh we need IBGE data" problem
(see `LESSONS_LEARNED.md` § 2.3, § 4.5).

### 3.4 Definition of Done

- [ ] Planner automatically includes IBGE data for geographic comparisons
- [ ] Planner automatically includes IPCA for cost analyses
- [ ] No mid-investigation data fetching needed

---

## Sprint 4 — Output Renderer

**Goal:** Generate human-readable outputs from the execution trace.
Notebooks are output, not execution (see `LESSONS_LEARNED.md` § 4.3).

### 4.1 Report Generator (`src/agent/renderer.py`)

Produces from the execution trace:
- **Markdown reports** — evidence → interpretation → implication structure
- **Inline chart references** — links to PNGs produced during analysis
- **Metrics JSON** — machine-readable key findings
- **Executive summary** — 1-page overview for policymakers

Uses the skill's FINDINGS.md template and output standards.

### 4.2 Notebook Generator

Reconstructs Jupyter notebooks from the execution trace:
- Each `CodeExecution` becomes a code cell
- Critic assessments become markdown cells
- Charts are embedded as image outputs
- Result: a runnable notebook that reproduces the investigation

### 4.3 Report Reflection

Self-evaluates the generated report before presenting to human:
- Is the narrative coherent?
- Are claims supported by evidence in the trace?
- Are there gaps in the story?
- Would the audience find this actionable?

### 4.4 Definition of Done

- [ ] Agent produces a markdown report from the execution trace
- [ ] Report follows skill's FINDINGS.md template
- [ ] Generated notebook is runnable and reproduces key outputs
- [ ] Report reflection catches at least 1 gap before human review

---

## Sprint 5 — Human Checkpoints + Depth-1 Recursion (RLM)

**Goal:** Add the three human review points and depth-1 sub-investigations
(the recursive half of the RLM pattern).

### 5.1 Human Checkpoints (`src/agent/checkpoint.py`)

Three pause points where the agent waits for human approval:

| Checkpoint | After | Human Sees | Human Can |
|---|---|---|---|
| CP1 | Plan + EDA | Plots, metrics, proposed hypotheses | Approve, redirect, add hypotheses |
| CP2 | Core analysis | Model metrics, SHAP, findings | Approve, request changes, flag leakage |
| CP3 | Before report | Draft report, exec summary | Approve, request revisions |

Implementation: serialize state, pause execution, present summary,
resume on human input.

### 5.2 Depth-1 Sub-Investigation (`src/agent/subagent.py`)

When the Critic or Phase Reflection flags a surprising finding, spawn a
child investigation:

```python
spawn_sub_investigation(
    question="Why does Guarulhos have 3x the ER rate?",
    context_variables=["df", "cnes"],
    max_iterations=15,
) → SubInvestigation
```

The child agent receives:
- Its own REPL environment with copies of parent's dataframes
- The skill context
- A focused sub-question
- Its own Critic + Accumulator
- Simplified graph (EDA + Reflect only, no ML/simulation)

**Depth limit: 1.** The child cannot call `spawn_sub_investigation`.
(arXiv 2603.02615: depth > 1 degrades quality.)

Child findings merge back into parent's Accumulator.

### 5.3 Definition of Done

- [ ] Agent pauses at checkpoint 1 and resumes on approval
- [ ] Agent spawns at least 1 sub-investigation when appropriate
- [ ] Sub-investigation findings merge back into parent accumulator
- [ ] Depth-1 limit enforced (child cannot spawn grandchildren)

---

## Sprint 6 — LangGraph Migration + Parallelism

**Goal:** Migrate from plain function orchestration to LangGraph for
state persistence, fan-out/fan-in, and checkpointing.

### 6.1 Graph Structure (`src/agent/graph.py`)

Implement the cyclic graph from `PRD.md`:
- Planner → Data Loader → REPL → Reflect → Checkpoint → Hypothesis
  Fan-Out → Fan-In → Reflect → ML → Checkpoint → Simulation → Report
  → Reflect → Checkpoint → Done
- Reflection nodes route back to earlier phases

### 6.2 State Persistence

LangGraph checkpoints (SQLite) persist the full `InvestigationState`.
Enables:
- Resume interrupted investigations
- Human checkpoint pauses (async review)
- Branching (try two directions from same state)

### 6.3 Fan-Out/Fan-In

Parallel hypothesis testing via LangGraph `Send()`:
- Hypothesis Generator produces N hypotheses
- Each tested independently in its own REPL node
- Round-based synchronization barrier
- Results aggregated for Phase Reflection

### 6.4 Definition of Done

- [ ] Agent state persists across interruptions
- [ ] Human checkpoint pauses resume correctly
- [ ] Multiple hypotheses tested in parallel via `Send()`
- [ ] Full investigation completes in < 2 hours

---

## Sprint 7 — Investigation Memory + Second Condition

**Goal:** Cross-investigation learning and validation on a new condition.

### 7.1 Investigation Memory (`src/agent/memory.py`)

After each investigation, extract and store key learnings:

```python
@dataclass
class InvestigationMemory:
    condition: str          # "J96", "N20", etc.
    key_findings: list[str] # "age dominates mortality for respiratory conditions"
    methodological: list[str]  # "hospital ranking requires case-mix adjustment"
    data_quirks: list[str]  # "SEXO is string, not int"
    useful_enrichments: list[str]  # "IBGE population data essential for geo comparisons"
```

At planning time, retrieve relevant memories:

```
Planning N20 investigation:
  Memory from J96: "check if age is a dominant factor"
  Memory from J96: "always case-mix adjust hospital comparisons"
  Memory from J96: "check for COVID-era effects"
  → Planner incorporates these as early analysis steps
```

Storage: JSON or SQLite in `memory/` directory.

### 7.2 Validation: Kidney Stone (N20)

Run the agent on kidney stone data and compare with the manual
investigation in `experiments/kidney/`:

| Finding | Expected | Source |
|---|---|---|
| Volume growth 41% | Match within 5% | NB02 |
| Ureteroscopy drives 64% of growth | Match within 5% | NB04 |
| Hospital efficiency variation | Qualitative match | NB06 |
| Reallocation model | Quantitative match | NB08 |

**Zero agent code changes** — only the research question changes.

### 7.3 Definition of Done

- [ ] Investigation memory persisted after J96 run
- [ ] Memory retrieved and used in N20 planning
- [ ] Agent produces equivalent findings to manual kidney stone investigation
- [ ] No agent code changes required
- [ ] FINDINGS.md is presentation-ready without manual editing

---

## Sprint 8 — MCP Integration + New Data Sources

**Goal:** Model Context Protocol servers for live data access and
standardized plotting.

### 8.1 DATASUS MCP Server (`src/mcp/datasus.py`)

```
Tools: query_sih, query_cnes, lookup_icd10, lookup_procedure, lookup_municipality
```

Enables SQL-like queries against DATASUS data without loading full
parquets. Useful for exploratory questions before committing to full
data loads.

### 8.2 Plotting MCP Server

```
Tools: bar_chart, time_series, shap_summary, executive_dashboard
```

Standardized research-quality plots. Consistent styling across
investigations.

### 8.3 New Data Sources

Add support for:
- SIM (mortality) — cross-reference deaths with admissions
- SINAN (diseases) — outbreak analysis
- SINASC (births) — maternal/neonatal health

### 8.4 Definition of Done

- [ ] Agent can query SIH via MCP without loading full parquets
- [ ] Agent can look up ICD-10 codes via MCP
- [ ] Test on a third condition (e.g., dengue) with no code changes

---

## Open Research Questions

These are ongoing challenges, not sprint deliverables:

1. **Surprise modeling** — How to build a model of "what the audience
   already knows" for the Critic's surprise test. Currently hardcoded
   domain priors from the skill. Could be learned from past investigations
   via memory.

2. **Policy imagination** — Bridging from statistics to actionable policy
   recommendations. The skill provides the investigation workflow but
   not the policy landscape. Currently relies on the LLM's general
   knowledge + audience profile from Planner.

3. **Critic calibration** — The Critic needs to be strict enough to catch
   real problems but lenient enough not to block good analyses. The
   pass/deepen/fail thresholds may need tuning per model. The eval
   framework (`eval/`) enables this tuning.

4. **Optimal model selection** — Cloud models (Claude, GPT-4o) are better
   Critics but add cost and latency. Local models (qwen3:8b) are fast but
   less accurate. Hybrid approaches (local for codegen, cloud for critic)
   may be optimal.

5. **Skill evolution** — As the agent runs more investigations, should the
   skill itself be updated? Investigation memory captures learnings, but
   integrating them back into the skill is a meta-learning problem.

---

## Document Index

| Doc | Purpose |
|---|---|
| `docs/agent/START_HERE.md` | Entry point — what exists, what to build, Sprint 0 scope |
| `docs/agent/LESSONS_LEARNED.md` | Five failure modes of AI research and the architecture to fix them |
| `docs/agent/ARCHITECTURE.md` | Technical architecture — Skills, RLM, Memory, graph structure |
| `docs/agent/ROADMAP.md` | This file — sprint plan with deliverables and DoD |
| `docs/agent/PRD.md` | Original PRD — LangGraph design, state schema, tools, MCP |
